import base64

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
    create_ref = respx.post("https://api.github.com/repos/o/r/git/refs").mock(
        return_value=httpx.Response(201, json={})
    )
    respx.put("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post("https://api.github.com/repos/o/r/pulls").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/7"})
    )
    url = github.open_pr("o", "r", "README.md", "filesha", "# New", base="main")
    assert url == "https://github.com/o/r/pull/7"
    # the new ref is a readmint/* branch, never the default
    body = create_ref.calls.last.request.content.decode()
    assert "refs/heads/readmint/refine-" in body


def test_disabled_raises(monkeypatch):
    monkeypatch.setattr(settings, "gh_app_id", "")
    with pytest.raises(RuntimeError):
        github._installation_token()
