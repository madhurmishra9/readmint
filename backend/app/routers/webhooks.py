"""POST /api/webhooks/github — score-on-push PR comment, no LLM call.

Wires the deterministic ``/api/score`` check into GitHub's webhook delivery,
for teams that want one centrally-run listener instead of the composite
Action in ``action.yml`` wired into every consuming repo's workflows. Only
``pull_request`` events are handled; everything else is acknowledged and
ignored so GitHub doesn't retry it as a failure.
"""
from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request

from ..config import settings
from ..core import scoring, templates
from ..services import github

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

_HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}
_MARKER = "<!-- readmint-score-comment -->"


def _verify_signature(body: bytes, signature: str | None) -> None:
    if not settings.gh_webhook_secret:
        return  # no secret configured — dev/local only, never in production
    if not signature or not signature.startswith("sha256="):
        raise HTTPException(401, "missing X-Hub-Signature-256")
    mac = hmac.new(settings.gh_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, signature[len("sha256="):]):
        raise HTTPException(401, "signature mismatch")


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    template: str | None = None,
):
    raw = await request.body()
    _verify_signature(raw, x_hub_signature_256)

    if x_github_event != "pull_request":
        return {"status": "ignored", "reason": f"event={x_github_event}"}

    payload = await request.json()
    if payload.get("action") not in _HANDLED_ACTIONS:
        return {"status": "ignored", "reason": f"action={payload.get('action')}"}

    pr = payload["pull_request"]
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    number = pr["number"]

    try:
        content, path, _sha = github.fetch_readme(owner, repo, pr["head"]["sha"])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"could not fetch README: {e}")

    tmpl = templates.load(template) if template else None
    result = scoring.score(content, tmpl)

    body = f"{_MARKER}\n**Readmint score** for `{path}`: {result['score']}/100"
    try:
        github.create_pr_comment(owner, repo, number, body)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"scored ok but comment failed: {e}")

    return {"status": "ok", "score": result["score"]}
