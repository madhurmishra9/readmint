"""Handle *many* READMEs — bounded worker pool over the sync pipeline.

Concurrency is capped (``RF_BATCH_CONCURRENCY``) to respect Cortex rate limits.
Inputs feeding ``documents``: a zip (walk for ``*.md``), one repo
(``github.fetch_readme``), or an org (iterate repos).
"""
from __future__ import annotations

import io
import zipfile
from typing import Dict, Optional

import anyio

from ..config import settings
from ..core import templates
from ..pipeline import run_pipeline


async def process_many(documents: Dict[str, str], *, template: Optional[dict] = None, opts: Optional[dict] = None) -> dict:
    results: Dict[str, dict] = {}
    limiter = anyio.CapacityLimiter(settings.batch_concurrency)

    async def worker(name: str, content: str):
        async with limiter:
            results[name] = await anyio.to_thread.run_sync(
                lambda: run_pipeline(content, template=template, opts=opts)
            )

    async with anyio.create_task_group() as tg:
        for name, content in documents.items():
            tg.start_soon(worker, name, content)
    return results


def documents_from_zip(blob: bytes) -> Dict[str, str]:
    """Walk a zip archive for markdown files."""
    docs: Dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".md", ".markdown")):
                continue
            with zf.open(info) as fh:
                docs[info.filename] = fh.read().decode("utf-8", errors="replace")
    return docs


def resolve_template(name: Optional[str]) -> Optional[dict]:
    return templates.load(name) if name else None
