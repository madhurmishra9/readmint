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

# Manifests the version-sync check knows how to read (core/version_sync.py).
_MANIFEST_FILES = ("pyproject.toml", "package.json", "go.mod", "Cargo.toml")


def _manifests(req: GithubRefineRequest, token: str | None) -> dict:
    """Best-effort manifest fetch for the version-sync check; a repo without a
    given manifest, or a transient API error, just means less to compare against."""
    if not req.options.check_version_sync:
        return {}
    manifests = {}
    for name in _MANIFEST_FILES:
        try:
            content = github.fetch_file(req.owner, req.repo, name, req.ref, token=token)
        except Exception:  # noqa: BLE001
            content = None
        if content is not None:
            manifests[name] = content
    return {"manifests": manifests}


def _expected_license(req: GithubRefineRequest, token: str | None) -> dict:
    """Best-effort repo license for the badge-staleness check; failure never
    breaks the refine — it just means the check has nothing to compare against."""
    if not req.options.check_badges:
        return {}
    try:
        return {"expected_license": github.get_license(req.owner, req.repo, token=token)}
    except Exception:  # noqa: BLE001
        return {"expected_license": None}


def _repo_files(req: GithubRefineRequest, token: str | None) -> dict:
    """Best-effort file tree for the doc-drift check; failure never breaks the
    refine — it just means the check reports nothing instead of a false positive."""
    if not req.options.check_drift:
        return {}
    try:
        return {"repo_files": github.list_repo_files(req.owner, req.repo, req.ref, token=token)}
    except Exception:  # noqa: BLE001
        return {"repo_files": None}


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
    opts.update(_repo_files(req, token))
    opts.update(_manifests(req, token))
    result = run_pipeline(content, template=tmpl, opts=opts)
    result["original"] = content
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
