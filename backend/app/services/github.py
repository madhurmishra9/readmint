"""GitHub integration — pull a README, open a PR.

Two auth modes, both reaching the same pull → branch → commit → PR flow that
NEVER pushes to the default branch:

* **PAT** — the caller supplies a Personal Access Token (per-request, bring your
  own token). Used directly as a bearer token.
* **GitHub App** — sign a short-lived JWT with the app private key and exchange
  it for an installation token (deployment-wide, configured via RF_GH_*).

When a token is passed explicitly it is a PAT and used as-is; otherwise the App
installation token is minted. Every call honours the corporate proxy + CA bundle.
"""
from __future__ import annotations

import base64
import time
from typing import Optional, Tuple

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


def _resolve_token(token: Optional[str]) -> str:
    """A caller-supplied PAT wins; otherwise mint a GitHub App installation token."""
    return token if token else _installation_token()


def verify_token(token: str) -> str:
    """Return the authenticated login for a PAT, raising on an invalid/expired token."""
    with _client() as c:
        r = c.get("/user", headers=_auth(token))
        r.raise_for_status()
        return r.json()["login"]


def fetch_readme(owner: str, repo: str, ref: str = "HEAD", *, token: Optional[str] = None) -> Tuple[str, str, str]:
    token = _resolve_token(token)
    with _client() as c:
        r = c.get(f"/repos/{owner}/{repo}/readme", params={"ref": ref}, headers=_auth(token))
        r.raise_for_status()
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["path"], data["sha"]


def _default_branch(c: httpx.Client, owner: str, repo: str, headers: dict) -> str:
    r = c.get(f"/repos/{owner}/{repo}", headers=headers)
    r.raise_for_status()
    return r.json()["default_branch"]


def open_pr(
    owner: str,
    repo: str,
    path: str,
    new_content: str,
    *,
    base: Optional[str] = None,
    token: Optional[str] = None,
) -> str:
    token = _resolve_token(token)
    branch = f"readmint/refine-{int(time.time())}"
    headers = _auth(token)
    with _client() as c:
        # Resolve the base branch from the repo when not given — never assume "main".
        if not base:
            base = _default_branch(c, owner, repo, headers)
        base_sha = c.get(f"/repos/{owner}/{repo}/git/ref/heads/{base}", headers=headers).json()["object"]["sha"]
        # The file sha must match the file *on the base branch*, not whatever ref
        # the content was originally read at (else the PUT 409s); 404 ⇒ new file.
        cur = c.get(f"/repos/{owner}/{repo}/contents/{path}", params={"ref": base}, headers=headers)
        sha = cur.json().get("sha") if cur.status_code < 400 else None
        c.post(
            f"/repos/{owner}/{repo}/git/refs",
            headers=headers,
            json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        ).raise_for_status()
        put_body = {
            "message": "docs: refine README via Readmint",
            "content": base64.b64encode(new_content.encode()).decode(),
            "branch": branch,
        }
        if sha:
            put_body["sha"] = sha
        c.put(f"/repos/{owner}/{repo}/contents/{path}", headers=headers, json=put_body).raise_for_status()
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
