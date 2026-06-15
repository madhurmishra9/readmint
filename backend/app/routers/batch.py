"""POST /api/batch — zip upload or JSON list → many results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..auth.rbac import User, current_user
from ..schemas import BatchListRequest
from ..services import batch, history

router = APIRouter(prefix="/api", tags=["batch"])


def _summarise(results: dict) -> dict:
    return {
        "count": len(results),
        "blocked": sum(1 for r in results.values() if r.get("status") == "blocked"),
        "unverified": sum(1 for r in results.values() if r.get("verified") is False),
    }


@router.post("/batch")
async def batch_json(req: BatchListRequest, user: User = Depends(current_user)):
    docs = {item.name: item.text for item in req.documents}
    tmpl = batch.resolve_template(req.options.template)
    results = await batch.process_many(docs, template=tmpl, opts=req.options.to_opts())
    for name, res in results.items():
        history.record(user.email, "batch", name, res)
    return {"summary": _summarise(results), "results": results}


@router.post("/batch/zip")
async def batch_zip(
    file: UploadFile = File(...),
    template: str | None = Form(default=None),
    check_links: bool = Form(default=False),
    allow_secrets: bool = Form(default=False),
    redact: bool = Form(default=False),
    user: User = Depends(current_user),
):
    blob = await file.read()
    try:
        docs = batch.documents_from_zip(blob)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"invalid zip: {e}")
    if not docs:
        raise HTTPException(400, "no .md files found in archive")
    tmpl = batch.resolve_template(template)
    opts = {"check_links": check_links, "allow_secrets": allow_secrets, "redact": redact, "use_cache": True}
    results = await batch.process_many(docs, template=tmpl, opts=opts)
    for name, res in results.items():
        history.record(user.email, "batch", name, res)
    return {"summary": _summarise(results), "results": results}
