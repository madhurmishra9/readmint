"""Per-org glossary normalisation — canonical product names and casing.

Deterministic, applied *before* the diff is shown so reviewers see consistent
terms. Crucially it never edits inside fenced/inline code or URLs — rewriting a
command or a link would itself be data loss.

Glossary shape: ``{canonical: [alias, ...]}``. Aliases are matched whole-word,
case-insensitively, and replaced with the canonical spelling.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# split the doc into code/url segments (protected) and prose (editable)
_PROTECT = re.compile(
    r"(```.*?```|`[^`\n]+`|https?://\S+|\[[^\]]*\]\([^)]*\))",
    re.S,
)


def _build_pattern(aliases: List[str]) -> re.Pattern:
    parts = sorted((re.escape(a) for a in aliases if a), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.I)


def normalize(md: str, glossary: Optional[Dict[str, List[str]]]) -> str:
    if not md or not glossary:
        return md
    compiled = [(canonical, _build_pattern(aliases)) for canonical, aliases in glossary.items() if aliases]
    if not compiled:
        return md

    def fix(segment: str) -> str:
        for canonical, pat in compiled:
            segment = pat.sub(canonical, segment)
        return segment

    out = []
    for chunk in _PROTECT.split(md):
        if not chunk:
            continue
        if _PROTECT.fullmatch(chunk):
            out.append(chunk)  # protected: leave verbatim
        else:
            out.append(fix(chunk))
    return "".join(out)
