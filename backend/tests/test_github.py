import base64
import json

import httpx
import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.services import github


@pytest.fixture
def gh_app(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    monkeypatch.setattr(settings, "gh_app_id", "123")
    monkeypatch.setattr(settings, "gh_installation_id", "456")
    monkeypatch.setattr(settings, "gh_private_key", pem)
    assert settings.github_enabled


@respx.mock
def test_fetch_readme(gh_app):
    respx.post("https://api.github.com/app/installations/456/access_tokens").mock(
        return_value=httpx.Response(201, json={"token": "tok"})
    )
    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(b"# Hello").decode(),
            "path": "README.md",
            "sha": "deadbeef",
        })
    )
    content, path, sha = github.fetch_readme("o", "r")
    assert content == "# Hello"
    assert path == "README.md"
    assert sha == "deadbeef"


@respx.mock
def test_open_pr_flow_branches_never_pushes_default(gh_app):
    respx.post("https://api.github.com/app/installations/456/access_tokens").mock(
        return_value=httpx.Response(201, json={"token": "tok"})
    )
    respx.get("https://api.github.com/repos/o/r/git/ref/heads/main").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "basesha"}})
    )
    # the file sha is read from the *base* branch (decoupled from the fetch ref)
    respx.get("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={"sha": "basefilesha"})
    )
    create_ref = respx.post("https://api.github.com/repos/o/r/git/refs").mock(
        return_value=httpx.Response(201, json={})
    )
    respx.put("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post("https://api.github.com/repos/o/r/pulls").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/7"})
    )
    url = github.open_pr("o", "r", "README.md", "# New", base="main")
    assert url == "https://github.com/o/r/pull/7"
    # the new ref is a readmint/* branch, never the default
    body = create_ref.calls.last.request.content.decode()
    assert "refs/heads/readmint/refine-" in body


@respx.mock
def test_open_pr_resolves_default_branch_when_base_omitted(gh_app):
    respx.post("https://api.github.com/app/installations/456/access_tokens").mock(
        return_value=httpx.Response(201, json={"token": "tok"})
    )
    # repo's default branch is NOT main — the PR must target it, not "main"
    respx.get("https://api.github.com/repos/o/r").mock(
        return_value=httpx.Response(200, json={"default_branch": "develop"})
    )
    respx.get("https://api.github.com/repos/o/r/git/ref/heads/develop").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "dsha"}})
    )
    respx.get("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={"sha": "f"})
    )
    respx.post("https://api.github.com/repos/o/r/git/refs").mock(
        return_value=httpx.Response(201, json={})
    )
    respx.put("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={})
    )
    pulls = respx.post("https://api.github.com/repos/o/r/pulls").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/9"})
    )
    url = github.open_pr("o", "r", "README.md", "# New")  # base omitted
    assert url.endswith("/pull/9")
    pr_body = json.loads(pulls.calls.last.request.content.decode())
    assert pr_body["base"] == "develop"


def test_disabled_raises(monkeypatch):
    monkeypatch.setattr(settings, "gh_app_id", "")
    with pytest.raises(RuntimeError):
        github._installation_token()


# --- PAT mode: a caller-supplied token is used directly, no App needed ---

@respx.mock
def test_fetch_readme_with_pat_skips_installation_token(monkeypatch):
    # No GitHub App configured — the PAT alone must drive the call.
    monkeypatch.setattr(settings, "gh_app_id", "")
    monkeypatch.setattr(settings, "gh_installation_id", "")
    monkeypatch.setattr(settings, "gh_private_key", "")
    install = respx.post("https://api.github.com/app/installations/456/access_tokens").mock(
        return_value=httpx.Response(201, json={"token": "tok"})
    )
    readme = respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(b"# Hello").decode(),
            "path": "README.md",
            "sha": "deadbeef",
        })
    )
    content, path, sha = github.fetch_readme("o", "r", token="ghp_pat")
    assert content == "# Hello"
    assert not install.called  # never minted an installation token
    assert readme.calls.last.request.headers["authorization"] == "Bearer ghp_pat"


@respx.mock
def test_verify_token_returns_login():
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat"})
    )
    assert github.verify_token("ghp_pat") == "octocat"


@respx.mock
def test_open_pr_with_pat_uses_token_and_branches(monkeypatch):
    monkeypatch.setattr(settings, "gh_app_id", "")
    respx.get("https://api.github.com/repos/o/r/git/ref/heads/main").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "basesha"}})
    )
    respx.get("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={"sha": "basefilesha"})
    )
    create_ref = respx.post("https://api.github.com/repos/o/r/git/refs").mock(
        return_value=httpx.Response(201, json={})
    )
    respx.put("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post("https://api.github.com/repos/o/r/pulls").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/11"})
    )
    url = github.open_pr("o", "r", "README.md", "# New", base="main", token="ghp_pat")
    assert url.endswith("/pull/11")
    assert create_ref.calls.last.request.headers["authorization"] == "Bearer ghp_pat"
    body = create_ref.calls.last.request.content.decode()
    assert "refs/heads/readmint/refine-" in body


@respx.mock
def test_get_license_returns_spdx_id():
    respx.get("https://api.github.com/repos/o/r/license").mock(
        return_value=httpx.Response(200, json={"license": {"spdx_id": "MIT"}})
    )
    assert github.get_license("o", "r", token="ghp_pat") == "MIT"


@respx.mock
def test_get_license_returns_none_when_unlicensed():
    respx.get("https://api.github.com/repos/o/r/license").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    assert github.get_license("o", "r", token="ghp_pat") is None
