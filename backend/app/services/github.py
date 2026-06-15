"""GitHub App integration — pull a README, open a PR.

GitHub App auth: sign a short-lived JWT with the app private key, exchange it
for an installation token. Every call honours the corporate proxy + CA bundle.
The PR flow is pull → branch → commit → PR; it NEVER pushes to the default
branch.
"""
from __future__ import annotations

import base64
import time
from typing import Tuple

import httpx
import jwt

from ..config import settings


def _require_app():
    if not settings.github_enabled:
        raise RuntimeError("GitHub App not configured (RF_GH_APP_ID / INSTALLATION_ID / PRIVATE_KEY)")


def _client() -> httpx.Client:
    return httpx.Client(
        proxy=settings.https_proxy or None,
        verify=settings.ca_bundle_path or True,
        timeout=30.0,
        base_url=settings.gh_api_base,
    )


def _installation_token() -> str:
    _require_app()
    now = int(time.time())
    assertion = jwt.encode(
        {"iat": now - 60, "exp": now + 540, "iss": settings.gh_app_id},
        settings.gh_private_key,
        algorithm="RS256",
    )
    with _client() as c:
        r = c.post(
            f"/app/installations/{settings.gh_installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {assertion}", "Accept": "application/vnd.github+json"},
        )
        r.raise_for_status()
        return r.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def fetch_readme(owner: str, repo: str, ref: str = "HEAD") -> Tuple[str, str, str]:
    token = _installation_token()
    with _client() as c:
        r = c.get(f"/repos/{owner}/{repo}/readme", params={"ref": ref}, headers=_auth(token))
        r.raise_for_status()
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["path"], data["sha"]


def open_pr(owner: str, repo: str, path: str, sha: str, new_content: str, base: str = "main") -> str:
    token = _installation_token()
    branch = f"readmint/refine-{int(time.time())}"
    headers = _auth(token)
    with _client() as c:
        base_sha = c.get(f"/repos/{owner}/{repo}/git/ref/heads/{base}", headers=headers).json()["object"]["sha"]
        c.post(
            f"/repos/{owner}/{repo}/git/refs",
            headers=headers,
            json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        ).raise_for_status()
        c.put(
            f"/repos/{owner}/{repo}/contents/{path}",
            headers=headers,
            json={
                "message": "docs: refine README via Readmint",
                "content": base64.b64encode(new_content.encode()).decode(),
                "sha": sha,
                "branch": branch,
            },
        ).raise_for_status()
        pr = c.post(
            f"/repos/{owner}/{repo}/pulls",
            headers=headers,
            json={
                "title": "docs: refine README via Readmint",
                "head": branch,
                "base": base,
                "body": "Automated README refinement. Content-preservation verified; see checks.",
            },
        )
        pr.raise_for_status()
        return pr.json()["html_url"]
