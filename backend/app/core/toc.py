"""Deterministic Table of Contents with correct GitHub anchors.

Never trust the LLM to compute anchors. GitHub slugs: lowercase, strip
punctuation (keep word chars, spaces, hyphens), spaces → hyphens, and append
``-1``, ``-2`` … to duplicate slugs in document order. ``ensure`` is idempotent:
re-running it replaces an existing ToC rather than stacking a second one.
"""
from __future__ import annotations

import re

_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*#*\s*$", re.M)
_TOC_HEADING = re.compile(r"^##\s+(?:table of contents|contents)\s*$", re.I | re.M)
_FENCED = re.compile(r"```.*?```", re.S)


def _slug(text: str, seen: dict) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    if s in seen:
        seen[s] += 1
        return f"{s}-{seen[s]}"
    seen[s] = 0
    return s


def build(md: str) -> str:
    """Return the ToC block (without inserting it), or '' if too few headings."""
    # Strip fenced code first so headings shown *inside* a code example
    # (common in docs-about-markdown) don't become bogus ToC entries.
    scan = _FENCED.sub("", md)
    headings = [(len(h), t.strip()) for h, t in _HEADING.findall(scan)]
    # skip a heading that *is* the ToC itself
    headings = [(lvl, t) for lvl, t in headings if t.strip().lower() not in ("table of contents", "contents")]
    if len(headings) < 3:
        return ""
    seen: dict = {}
    lines = ["## Table of Contents"]
    for level, text in headings:
        indent = "  " * (level - 2)
        lines.append(f"{indent}- [{text}](#{_slug(text, seen)})")
    return "\n".join(lines)


def ensure(md: str) -> str:
    toc = build(md)
    if not toc:
        return md

    m = _TOC_HEADING.search(md)
    if m:
        # replace from the ToC heading up to the next ## heading (or end of doc)
        start = m.start()
        nxt = re.search(r"^##\s+", md[m.end():], re.M)
        end = m.end() + nxt.start() if nxt else len(md)
        return md[:start] + toc + "\n\n" + md[end:].lstrip("\n")

    # insert after the first line (the title)
    parts = md.split("\n", 1)
    rest = parts[1].lstrip("\n") if len(parts) > 1 else ""
    return parts[0] + "\n\n" + toc + "\n\n" + rest
