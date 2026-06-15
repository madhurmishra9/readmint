import io
import zipfile

import pytest
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


def test_github_disabled_returns_503():
    r = client.post("/api/github/refine", json={"owner": "o", "repo": "r"})
    assert r.status_code == 503
