"""LLM change-summary — one low-temperature call returning 3-5 bullets."""
from __future__ import annotations

from .. import prompts
from ..cortex_client import cortex


def summarize(before: str, after: str) -> str:
    return cortex.complete(
        prompts.SUMMARY_SYSTEM,
        prompts.summary_user(before, after),
        temperature=0.0,
    ).strip()
