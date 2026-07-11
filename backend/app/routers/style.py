"""POST /api/style — deterministic prose/style lint, no LLM call."""
from __future__ import annotations

from fastapi import APIRouter

from ..core import style as style_core
from ..schemas import ScoreRequest

router = APIRouter(prefix="/api", tags=["style"])


@router.post("/style")
async def lint(req: ScoreRequest):
    return style_core.lint(req.text)
