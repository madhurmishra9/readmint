"""POST /api/github/refine — pull a repo README, refine, optionally open a PR."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth.rbac import User, current_user
from ..config import settings
from ..core import templates
from ..pipeline import run_pipeline
from ..schemas import GithubRefineRequest
from ..services import github, history

router = APIRouter(prefix="/api/github", tags=["github"])


def _expected_license(req: GithubRefineRequest, token: str | None) -> dict:
    """Best-effort repo license for the badge-staleness check; failure never
    breaks the refine — it just means the check has nothing to compare against."""
    if not req.options.check_badges:
        return {}
    try:
        return {"expected_license": github.get_license(req.owner, req.repo, token=token)}
    except Exception:  # noqa: BLE001
        return {"expected_license": None}


@router.post("/refine")
async def github_refine(req: GithubRefineRequest, user: User = Depends(current_user)):
    # A per-request PAT lets a user bring their own token; otherwise fall back to
    # a deployment-wide GitHub App. At least one must be available.
    token = req.pat or None
    if not token and not settings.github_enabled:
        raise HTTPException(503, "Provide a GitHub Personal Access Token, or configure a GitHub App on this deployment")
    if token:
        try:
            github.verify_token(token)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(401, f"GitHub token rejected: {e}")

    try:
        content, path, _sha = github.fetch_readme(req.owner, req.repo, req.ref, token=token)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"could not fetch README: {e}")

    tmpl = templates.load(req.options.template) if req.options.template else None
    opts = req.options.to_opts()
    opts.update(_expected_license(req, token))
    result = run_pipeline(content, template=tmpl, opts=opts)
    target = f"{req.owner}/{req.repo}:{path}"
    history.record(user.email, "github", target, result)

    if result.get("status") == "blocked":
        return result
    if not result.get("verified"):
        result["pr_url"] = None
        result["pr_skipped_reason"] = "content-preservation not verified"
        return result

    if req.open_pr:
        try:
            result["pr_url"] = github.open_pr(
                req.owner, req.repo, path, result["markdown"], base=req.base, token=token
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(502, f"refined ok but PR failed: {e}")
    return result
