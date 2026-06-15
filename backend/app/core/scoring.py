"""Deterministic completeness score, so before/after is trustworthy & comparable.

Two modes:
* default rubric — generic README quality (title, install, usage, license, ...).
* template mode — score required sections of an org template (governance).
"""
from __future__ import annotations

import re
from typing import Optional

RUBRIC = {
    "title": (10, lambda md: bool(re.search(r"^\s*#\s+\S", md, re.M))),
    "description": (10, lambda md: len(md.split("\n\n", 2)) > 1),
    "toc": (5, lambda md: "## table of contents" in md.lower() or "## contents" in md.lower()),
    "installation": (15, lambda md: bool(re.search(r"^#{1,3}\s*(install|setup|getting started)", md, re.I | re.M))),
    "usage": (15, lambda md: bool(re.search(r"^#{1,3}\s*(usage|quick ?start|example)", md, re.I | re.M))),
    "configuration": (10, lambda md: bool(re.search(r"^#{1,3}\s*config", md, re.I | re.M))),
    "code_examples": (10, lambda md: "```" in md),
    "license": (10, lambda md: bool(re.search(r"^#{1,3}\s*licen[sc]e", md, re.I | re.M))),
    "badges": (5, lambda md: bool(re.search(r"!\[[^\]]*\]\(https?://img\.shields\.io", md))),
    "headings_depth": (10, lambda md: len(set(re.findall(r"^(#{1,6})\s", md, re.M))) >= 2),
}


def _heading_present(md: str, heading: str) -> bool:
    pat = r"^#{1,6}\s*" + re.escape(heading.strip()) + r"\b"
    return bool(re.search(pat, md, re.I | re.M))


def score(md: str, template: Optional[dict] = None) -> dict:
    md = md or ""
    if template:
        return _score_template(md, template)
    breakdown, total, gained = {}, 0, 0
    for name, (weight, check) in RUBRIC.items():
        ok = bool(check(md))
        breakdown[name] = {"weight": weight, "passed": ok}
        total += weight
        gained += weight if ok else 0
    return {"score": round(100 * gained / total) if total else 0, "breakdown": breakdown, "mode": "rubric"}


def _score_template(md: str, template: dict) -> dict:
    sections = template.get("sections", [])
    breakdown, total, gained = {}, 0, 0
    for s in sections:
        heading = s["heading"]
        weight = 10 if s.get("required") else 5
        ok = _heading_present(md, heading)
        breakdown[heading] = {"weight": weight, "passed": ok, "required": bool(s.get("required"))}
        total += weight
        gained += weight if ok else 0
    return {
        "score": round(100 * gained / total) if total else 0,
        "breakdown": breakdown,
        "mode": "template",
        "template": template.get("name"),
    }
