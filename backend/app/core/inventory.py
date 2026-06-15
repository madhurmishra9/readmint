"""Content-preservation guard — *the spine*.

The LLM is allowed to reorganise, retitle and reword prose freely. It is **not**
allowed to drop data. We make that distinction enforceable by extracting an
inventory of *data-bearing atoms* — things whose disappearance is genuine loss —
and treating their wording/order as irrelevant:

    code blocks · inline code · URLs · image refs · numbers/versions · emails

Each atom is normalised then counted in a ``Counter`` so duplicates are tracked
(losing one of three identical commands is still loss). ``diff`` reports atoms
present in the *before* document that are missing (or fewer) in the *after*
document. Prose is deliberately **not** inventoried, so rewriting a sentence is
never flagged.

The same object also exposes ``.urls`` for the dead-link checker.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List

# --- extraction patterns ---------------------------------------------------
_FENCED = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_INDENTED = re.compile(r"(?:^|\n)((?: {4}|\t)[^\n]+(?:\n(?: {4}|\t)[^\n]+)*)")
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
_MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)")
_BARE_URL = re.compile(r"<?(https?://[^\s>)\]]+)>?")
_REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.M)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# Numbers that carry meaning: versions, ports, counts. Ignore pure markdown
# heading markers / list bullets by requiring a digit run of its own.
_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)*(?![\w])")

# Categories whose loss is, by policy, blocking. Numbers/emails are tracked and
# also count as loss (a dropped version or contact is real), but are listed
# separately so the UI can show them distinctly.
CATEGORIES = ("code_blocks", "inline_code", "urls", "images", "numbers", "emails")


def _strip_url(u: str) -> str:
    return u.rstrip(".,);:'\"").strip()


@dataclass
class Inventory:
    code_blocks: Counter = field(default_factory=Counter)
    inline_code: Counter = field(default_factory=Counter)
    urls: Counter = field(default_factory=Counter)
    images: Counter = field(default_factory=Counter)
    numbers: Counter = field(default_factory=Counter)
    emails: Counter = field(default_factory=Counter)

    def as_map(self) -> Dict[str, Counter]:
        return {c: getattr(self, c) for c in CATEGORIES}


def _norm_code(block: str) -> str:
    """Whitespace-insensitive normalisation so reformatting isn't 'loss'."""
    return "\n".join(line.rstrip() for line in block.strip("\n").splitlines()).strip()


def extract(md: str) -> Inventory:
    md = md or ""
    inv = Inventory()

    # Code blocks first; remove them so their contents don't double-count as
    # inline code / urls / numbers living inside the snippet.
    code_spans: List[tuple[int, int]] = []
    for m in _FENCED.finditer(md):
        body = _norm_code(m.group(1))
        if body:
            inv.code_blocks[body] += 1
        code_spans.append(m.span())

    def _in_code(pos: int) -> bool:
        return any(a <= pos < b for a, b in code_spans)

    for m in _INLINE_CODE.finditer(md):
        if _in_code(m.start()):
            continue
        token = m.group(1).strip()
        if token:
            inv.inline_code[token] += 1

    for m in _IMAGE.finditer(md):
        inv.images[_strip_url(m.group(1))] += 1

    for rx in (_MD_LINK, _BARE_URL, _REF_DEF):
        for m in rx.finditer(md):
            url = _strip_url(m.group(1))
            if url and not url.startswith("#"):
                inv.urls[url] += 1

    for m in _EMAIL.finditer(md):
        # emails inside a URL (mailto:) already captured; this catches plain ones
        if not _in_code(m.start()):
            inv.emails[m.group(0).lower()] += 1

    for m in _NUMBER.finditer(md):
        if _in_code(m.start()):
            continue
        inv.numbers[m.group(0)] += 1

    return inv


def diff(before: Inventory, after: Inventory) -> Dict[str, List[str]]:
    """Atoms present in *before* but missing/reduced in *after*.

    Uses multiset subtraction so a dropped duplicate is still reported.
    """
    bmap, amap = before.as_map(), after.as_map()
    report: Dict[str, List[str]] = {}
    for cat in CATEGORIES:
        lost = bmap[cat] - amap[cat]  # Counter subtraction drops <=0 counts
        items: List[str] = []
        for value, count in lost.items():
            items.extend([value] * count)
        report[cat] = items
    return report


def has_loss(report: Dict[str, List[str]]) -> bool:
    return any(report.get(cat) for cat in CATEGORIES)


def summarize_loss(report: Dict[str, List[str]]) -> str:
    """Human/LLM-readable description of what went missing (for repair prompt)."""
    parts = []
    for cat in CATEGORIES:
        items = report.get(cat) or []
        if items:
            shown = ", ".join(repr(i[:80]) for i in items[:10])
            more = f" (+{len(items) - 10} more)" if len(items) > 10 else ""
            parts.append(f"- {cat}: {shown}{more}")
    return "\n".join(parts)
