import base64
import io
import zipfile

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DOC = "# tool\n\nintro\n\n## Install\n`pip install tool`\n\n## Usage\n```\ntool run\n```\nsee https://example.com\n"


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "addons" in r.json()


def test_score_endpoint_no_llm():
    r = client.post("/api/score", json={"text": DOC})
    assert r.status_code == 200
    assert 0 <= r.json()["score"] <= 100


def test_style_endpoint_no_llm():
    r = client.post("/api/style", json={"text": "In order to run this, do X.\n"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(f["rule"] == "wordy_phrase" for f in body["findings"])


def test_refine_with_check_style_attaches_report():
    r = client.post("/api/refine", data={"text": DOC, "check_style": "true"})
    assert r.status_code == 200
    assert r.json()["style"] is not None


def test_refine_without_check_style_omits_report():
    r = client.post("/api/refine", data={"text": DOC})
    assert r.status_code == 200
    assert r.json()["style"] is None


def test_refine_with_check_badges_attaches_report():
    md = "# tool\n\n![license](https://img.shields.io/badge/license-MIT-blue)\n"
    r = client.post("/api/refine", data={"text": md, "check_badges": "true"})
    assert r.status_code == 200
    body = r.json()
    assert body["badges"]["checked"] == 1


def test_refine_without_check_badges_omits_report():
    r = client.post("/api/refine", data={"text": DOC})
    assert r.status_code == 200
    assert r.json()["badges"] is None


def test_refine_paste():
    r = client.post("/api/refine", data={"text": DOC})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["verified"] is True
    assert "tool run" in body["markdown"]


def test_refine_requires_input():
    r = client.post("/api/refine", data={})
    assert r.status_code == 400


def test_refine_blocked_on_secret():
    r = client.post("/api/refine", data={"text": DOC + "\nAKIAIOSFODNN7EXAMPLE\n"})
    assert r.status_code == 200
    assert r.json()["status"] == "blocked"


def test_refine_file_upload():
    files = {"file": ("README.md", DOC.encode(), "text/markdown")}
    r = client.post("/api/refine", files=files)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_batch_json():
    payload = {"documents": [{"name": "a.md", "text": DOC}, {"name": "b.md", "text": "# b\n\nx"}]}
    r = client.post("/api/batch", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["count"] == 2
    assert set(body["results"].keys()) == {"a.md", "b.md"}


def test_batch_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("docs/README.md", DOC)
        zf.writestr("ignore.txt", "not markdown")
    buf.seek(0)
    r = client.post("/api/batch/zip", files={"file": ("b.zip", buf.read(), "application/zip")})
    assert r.status_code == 200
    assert r.json()["summary"]["count"] == 1


def test_export_html():
    r = client.post("/api/export", json={"markdown": "# Title\n\ntext", "format": "html"})
    assert r.status_code == 200
    assert "<h1>Title</h1>" in r.text


def test_export_unknown_format():
    r = client.post("/api/export", json={"markdown": "x", "format": "xyz"})
    assert r.status_code == 400


def test_history_records_runs():
    client.post("/api/refine", data={"text": DOC})
    r = client.get("/api/history")
    assert r.status_code == 200
    assert any(run["action"] == "refine" for run in r.json()["runs"])


def test_llm_info_endpoint():
    # Tests run with RF_LLM_STUB=true ⇒ provider is the stub, no models.
    r = client.get("/api/llm")
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] in {"stub", "cortex", "local"}
    assert "models" in body and "selected" in body


@respx.mock
def test_github_refine_check_drift_flags_missing_file():
    content = "# tool\n\nRun `scripts/build.sh` to build.\n"
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat"})
    )
    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(content.encode()).decode(), "path": "README.md", "sha": "s",
        })
    )
    respx.get("https://api.github.com/repos/o/r/git/trees/HEAD").mock(
        return_value=httpx.Response(200, json={"tree": [{"path": "README.md", "type": "blob"}]})
    )
    r = client.post(
        "/api/github/refine",
        json={"owner": "o", "repo": "r", "open_pr": False, "pat": "ghp_token",
              "options": {"check_drift": True}},
    )
    assert r.status_code == 200, r.text
    assert "scripts/build.sh" in r.json()["drift"]["missing"]


@respx.mock
def test_github_refine_check_version_sync_flags_mismatch():
    content = "# tool\n\nRequires Python 3.9+.\n"
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat"})
    )
    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(content.encode()).decode(), "path": "README.md", "sha": "s",
        })
    )
    respx.get("https://api.github.com/repos/o/r/contents/pyproject.toml").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(b'requires-python = ">=3.11"').decode(),
        })
    )
    for name in ("package.json", "go.mod", "Cargo.toml"):
        respx.get(f"https://api.github.com/repos/o/r/contents/{name}").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
    r = client.post(
        "/api/github/refine",
        json={"owner": "o", "repo": "r", "open_pr": False, "pat": "ghp_token",
              "options": {"check_version_sync": True}},
    )
    assert r.status_code == 200, r.text
    assert r.json()["version_sync"]["mismatches"][0]["manifest_version"] == "3.11"


def test_github_disabled_returns_503():
    r = client.post("/api/github/refine", json={"owner": "o", "repo": "r"})
    assert r.status_code == 503


@respx.mock
def test_github_refine_check_badges_uses_repo_license():
    content = "# tool\n\n![license](https://img.shields.io/badge/license-Apache--2.0-blue)\n"
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat"})
    )
    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(content.encode()).decode(), "path": "README.md", "sha": "s",
        })
    )
    respx.get("https://api.github.com/repos/o/r/license").mock(
        return_value=httpx.Response(200, json={"license": {"spdx_id": "MIT"}})
    )
    r = client.post(
        "/api/github/refine",
        json={"owner": "o", "repo": "r", "open_pr": False, "pat": "ghp_token",
              "options": {"check_badges": True}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["badges"]["stale"][0]["reason"].startswith("badge says 'Apache-2.0'")


@respx.mock
def test_github_refine_with_pat_opens_pr():
    """A user-supplied PAT drives fetch → refine → branch → commit → PR end-to-end."""
    respx.get("https://api.github.com/user").mock(
        return_value=httpx.Response(200, json={"login": "octocat"})
    )
    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(DOC.encode()).decode(),
            "path": "README.md",
            "sha": "src",
        })
    )
    respx.get("https://api.github.com/repos/o/r").mock(
        return_value=httpx.Response(200, json={"default_branch": "main"})
    )
    respx.get("https://api.github.com/repos/o/r/git/ref/heads/main").mock(
        return_value=httpx.Response(200, json={"object": {"sha": "basesha"}})
    )
    respx.get("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={"sha": "filesha"})
    )
    respx.post("https://api.github.com/repos/o/r/git/refs").mock(
        return_value=httpx.Response(201, json={})
    )
    respx.put("https://api.github.com/repos/o/r/contents/README.md").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post("https://api.github.com/repos/o/r/pulls").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/42"})
    )
    r = client.post(
        "/api/github/refine",
        json={"owner": "o", "repo": "r", "open_pr": True, "pat": "ghp_token"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["pr_url"] == "https://github.com/o/r/pull/42"


@respx.mock
def test_github_refine_rejects_bad_pat():
    respx.get("https://api.github.com/user").mock(return_value=httpx.Response(401, json={}))
    r = client.post("/api/github/refine", json={"owner": "o", "repo": "r", "pat": "bad"})
    assert r.status_code == 401
