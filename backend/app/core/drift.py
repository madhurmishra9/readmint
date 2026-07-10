"""Doc-drift detection — no LLM, no network.

Extends the no-loss philosophy from "never drop content" to "never keep
content that is no longer *true*": a README that still tells readers to run
``scripts/build.sh`` after that script was deleted has drifted from the
codebase it describes. This module looks inside inline code spans, fenced
code blocks, and relative markdown links for path-like tokens, and checks
each one against the repo's real file tree. The tree must be supplied by the
caller (e.g. a GitHub Git Trees API listing); this module does no I/O.
"""
from __future__ import annotations

import re
from typing import Iterable, Set

_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_FENCED = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")

# "word/word[/word...]", optionally with a file extension, no URL scheme.
_PATH_LIKE = re.compile(r"^[\w.\-]+(?:/[\w.\-]+)+/?$")
_STRIP = "`'\",.()[]{}:;<>"


def _candidate_paths(text: str) -> Set[str]:
    out = set()
    for token in text.split():
        token = token.strip(_STRIP)
        if not token or token.startswith(("http://", "https://", "@")):
            continue
        if _PATH_LIKE.match(token):
            out.add(token.rstrip("/"))
    return out


def extract_references(md: str) -> Set[str]:
    refs: Set[str] = set()
    for m in _INLINE_CODE.finditer(md or ""):
        refs |= _candidate_paths(m.group(1))
    for m in _FENCED.finditer(md or ""):
        refs |= _candidate_paths(m.group(1))
    for m in _MD_LINK.finditer(md or ""):
        target = m.group(1).split("#")[0]
        if target and not target.startswith(("http://", "https://", "mailto:")):
            refs.add(target.rstrip("/"))
    return refs


def _exists(ref: str, existing: Set[str]) -> bool:
    if ref in existing:
        return True
    prefix = ref.rstrip("/") + "/"
    return any(p.startswith(prefix) for p in existing)  # ref is a directory that still has files


def check(md: str, existing_paths: Iterable[str]) -> dict:
    existing = {p.lstrip("./") for p in existing_paths}
    refs = extract_references(md)
    missing = sorted(r for r in refs if not _exists(r, existing))
    return {"checked": len(refs), "missing": missing}
