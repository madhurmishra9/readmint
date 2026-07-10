"""Deterministic prose/style lint — no LLM, no network.

Catches what a human reviewer flags by eye: wordy filler phrases,
passive-voice hedging, overlong sentences, images with no alt text, and
formatting slop (trailing whitespace, stacked blank lines). Findings are
advisory — they never block the pipeline and are not part of the
completeness score (``scoring.py``); a wordy README can still be complete.

Fenced code blocks are excluded so example commands/output are never
mistaken for prose.
"""
from __future__ import annotations

import re
from typing import List, Optional

_FENCED = re.compile(r"```[^\n]*\n.*?```", re.S)

# phrase -> a tighter alternative, shown in the finding as a suggestion
_WORDY_PHRASES = {
    "in order to": "to",
    "a number of": "several",
    "due to the fact that": "because",
    "at this point in time": "now",
    "for the purpose of": "to",
    "in the event that": "if",
    "is able to": "can",
    "with regard to": "about",
    "utilize": "use",
    "utilizes": "uses",
    "utilizing": "using",
    "leverage": "use",
}

# Heuristic, not a grammar parser: "is/was/were ... <verb>ed" reads as passive.
_PASSIVE_RE = re.compile(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", re.I)
_EMPTY_ALT_IMAGE = re.compile(r"!\[\s*\]\([^)]+\)")
_SENTENCE_END = re.compile(r"[.!?]\s*$")

MAX_SENTENCE_WORDS = 40
MAX_BLANK_LINES = 2


def _blank_code_blocks(md: str) -> str:
    """Replace fenced code with inert placeholder lines, preserving line numbers.

    Placeholder lines are non-blank on purpose: swapping code for real blank
    lines would let a fence glue onto neighbouring blank lines and produce a
    false ``multiple_blank_lines`` finding.
    """
    def repl(m: "re.Match[str]") -> str:
        n = m.group(0).count("\n")
        return "\n".join(["\x00"] * (n + 1))

    return _FENCED.sub(repl, md)


def _add(findings: List[dict], rule: str, line: Optional[int], message: str) -> None:
    findings.append({"rule": rule, "line": line, "message": message})


def lint(md: str) -> dict:
    md = md or ""
    prose = _blank_code_blocks(md)
    lines = prose.splitlines()
    findings: List[dict] = []

    blank_run = 0
    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            blank_run += 1
            if blank_run == MAX_BLANK_LINES + 1:
                _add(findings, "multiple_blank_lines", i, f"more than {MAX_BLANK_LINES} consecutive blank lines")
            continue
        blank_run = 0

        if line != line.rstrip():
            _add(findings, "trailing_whitespace", i, "trailing whitespace")

        lower = line.lower()
        for phrase, suggestion in _WORDY_PHRASES.items():
            if phrase in lower:
                _add(findings, "wordy_phrase", i, f'"{phrase}" — consider "{suggestion}"')

        for m in _EMPTY_ALT_IMAGE.finditer(line):
            _add(findings, "missing_alt_text", i, "image has empty alt text")

        # Only lint lines that look like prose sentences, not headings/tables/lists.
        stripped = line.strip()
        if stripped.startswith(("#", "|", "-", "*", "```")) or not _SENTENCE_END.search(stripped):
            continue

        for sentence in re.split(r"(?<=[.!?])\s+", stripped):
            words = sentence.split()
            if len(words) > MAX_SENTENCE_WORDS:
                _add(findings, "long_sentence", i, f"{len(words)}-word sentence — consider splitting")
            if _PASSIVE_RE.search(sentence):
                _add(findings, "passive_voice", i, sentence[:100])

    return {"checked": True, "count": len(findings), "findings": findings}
