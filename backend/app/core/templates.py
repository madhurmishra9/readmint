"""Org template loader + section mapper (governance).

A template is YAML: a ``name`` plus an ordered ``sections`` list of
``{heading, required}``. The parsed dict is passed into ``prompts.system_for``
(so the LLM reshapes content to fit) and into ``scoring.score`` (so completeness
is measured against the template instead of the generic rubric).

Templates also carry a ``doc_type`` (default ``"readme"``), so the same
governance machinery — section contracts, template-mode scoring, prompt
shaping — applies to companion docs (``CONTRIBUTING.md``, ``SECURITY.md``,
``CODE_OF_CONDUCT.md``) without any code changes: dropping in a new YAML
with ``doc_type: contributing`` is enough to register it.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import List, Optional

import yaml

from ..config import settings


def _dir() -> Path:
    p = Path(settings.templates_dir)
    if not p.is_absolute():
        # resolve relative to the backend package root (parent of app/)
        p = Path(__file__).resolve().parents[2] / settings.templates_dir
    return p


def list_templates(doc_type: Optional[str] = None) -> List[str]:
    d = _dir()
    if not d.exists():
        return []
    names = sorted(p.stem for p in d.glob("*.y*ml"))
    if doc_type is None:
        return names
    return [n for n in names if (load(n) or {}).get("doc_type") == doc_type]


def list_doc_types() -> List[str]:
    d = _dir()
    if not d.exists():
        return []
    return sorted({(load(p.stem) or {}).get("doc_type", "readme") for p in d.glob("*.y*ml")})


@functools.lru_cache(maxsize=64)
def load(name: Optional[str]) -> Optional[dict]:
    if not name:
        return None
    d = _dir()
    for ext in (".yaml", ".yml"):
        path = d / f"{name}{ext}"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return _validate(data, name)
    raise FileNotFoundError(f"template '{name}' not found in {d}")


def _validate(data: dict, name: str) -> dict:
    sections = []
    for s in data.get("sections", []):
        if isinstance(s, str):
            sections.append({"heading": s, "required": True})
        else:
            sections.append({"heading": s["heading"], "required": bool(s.get("required", False))})
    return {
        "name": data.get("name", name),
        "doc_type": data.get("doc_type", "readme"),
        "sections": sections,
    }
