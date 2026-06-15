"""POST /api/score — deterministic completeness score, no LLM call."""
from __future__ import annotations

from fastapi import APIRouter

from ..core import scoring, templates
from ..schemas import ScoreRequest

router = APIRouter(prefix="/api", tags=["score"])


@router.post("/score")
async def score(req: ScoreRequest):
    tmpl = templates.load(req.template) if req.template else None
    return scoring.score(req.text, tmpl)
