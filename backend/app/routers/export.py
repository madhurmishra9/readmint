"""POST /api/export — HTML / PDF download, or push to Confluence."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response

from ..auth.rbac import User, current_user
from ..schemas import ExportRequest
from ..services import export

router = APIRouter(prefix="/api", tags=["export"])


@router.post("/export")
async def do_export(req: ExportRequest, user: User = Depends(current_user)):
    fmt = req.format.lower()
    if fmt == "html":
        return HTMLResponse(export.to_html(req.markdown, req.title))
    if fmt == "pdf":
        try:
            pdf = export.to_pdf(req.markdown, req.title)
        except RuntimeError as e:
            raise HTTPException(501, str(e))
        return Response(
            pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{req.title}.pdf"'},
        )
    if fmt == "confluence":
        try:
            return export.to_confluence(req.markdown, req.title, req.space, req.parent_id)
        except RuntimeError as e:
            raise HTTPException(503, str(e))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(502, f"Confluence push failed: {e}")
    raise HTTPException(400, f"unknown format '{req.format}' (html|pdf|confluence)")
