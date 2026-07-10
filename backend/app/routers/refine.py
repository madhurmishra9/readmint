"""POST /api/refine — single README through the full pipeline.

Accepts pasted text or an uploaded file (multipart or urlencoded form), so the
browser, the CLI, and pre-commit can all use the same endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..auth.rbac import User, current_user
from ..core import templates
from ..pipeline import run_pipeline
from ..services import history

router = APIRouter(prefix="/api", tags=["refine"])


@router.post("/refine")
async def refine(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    template: str | None = Form(default=None),
    check_links: bool = Form(default=False),
    check_style: bool = Form(default=False),
    check_badges: bool = Form(default=False),
    summary: bool = Form(default=False),
    allow_secrets: bool = Form(default=False),
    redact: bool = Form(default=False),
    model: str | None = Form(default=None),
    user: User = Depends(current_user),
):
    content = text
    name = "pasted.md"
    if file is not None:
        content = (await file.read()).decode("utf-8", errors="replace")
        name = file.filename or name
    if not content or not content.strip():
        raise HTTPException(400, "provide `text` or a `file`")

    tmpl = templates.load(template) if template else None
    result = run_pipeline(
        content,
        template=tmpl,
        opts={
            "check_links": check_links,
            "check_style": check_style,
            "check_badges": check_badges,
            "summary": summary,
            "allow_secrets": allow_secrets,
            "redact": redact,
            "model": model,
        },
    )
    history.record(user.email, "refine", name, result)
    return result
