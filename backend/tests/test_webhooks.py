import base64
import hashlib
import hmac
import json

import httpx
import respx
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

DOC = "# tool\n\n## Usage\nrun it\n"


def _pr_payload(action="opened"):
    return {
        "action": action,
        "pull_request": {"number": 7, "head": {"sha": "abc123"}},
        "repository": {"owner": {"login": "o"}, "name": "r"},
    }


@respx.mock
def test_webhook_scores_and_comments(monkeypatch):
    monkeypatch.setattr(settings, "gh_app_id", "1")
    monkeypatch.setattr(settings, "gh_installation_id", "2")
    monkeypatch.setattr(settings, "gh_private_key", "")
    monkeypatch.setattr(settings, "gh_webhook_secret", "")
    # avoid signing a JWT for a fake key — bypass installation token via a PAT-shaped call instead
    import app.services.github as gh_mod
    monkeypatch.setattr(gh_mod, "_resolve_token", lambda token: token or "ghp_fake")

    respx.get("https://api.github.com/repos/o/r/readme").mock(
        return_value=httpx.Response(200, json={
            "content": base64.b64encode(DOC.encode()).decode(), "path": "README.md", "sha": "s",
        })
    )
    comment = respx.post("https://api.github.com/repos/o/r/issues/7/comments").mock(
        return_value=httpx.Response(201, json={"html_url": "https://github.com/o/r/pull/7#issuecomment-1"})
    )

    r = client.post(
        "/api/webhooks/github",
        json=_pr_payload(),
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"
    assert "score" in r.json()
    posted_body = json.loads(comment.calls.last.request.content.decode())["body"]
    assert "Readmint score" in posted_body


def test_webhook_ignores_non_pull_request_events():
    r = client.post("/api/webhooks/github", json={}, headers={"X-GitHub-Event": "push"})
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_webhook_ignores_unhandled_actions():
    r = client.post(
        "/api/webhooks/github",
        json=_pr_payload(action="closed"),
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_webhook_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(settings, "gh_webhook_secret", "s3cret")
    body = json.dumps(_pr_payload()).encode()
    r = client.post(
        "/api/webhooks/github",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "Content-Type": "application/json",
                 "X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert r.status_code == 401


def test_webhook_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(settings, "gh_webhook_secret", "s3cret")
    body = json.dumps({"action": "closed", "pull_request": {"number": 1},
                        "repository": {"owner": {"login": "o"}, "name": "r"}}).encode()
    sig = "sha256=" + hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    r = client.post(
        "/api/webhooks/github",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "Content-Type": "application/json",
                 "X-Hub-Signature-256": sig},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"  # action "closed" isn't handled, but signature passed
