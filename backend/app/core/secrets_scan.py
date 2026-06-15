"""Egress gate — nothing reaches Cortex until it's checked.

The highest-priority guard in a banking context. ``scan`` finds secrets/PII via
regex + Shannon-entropy heuristics; ``redact`` rewrites them while preserving
surrounding structure (so a redacted README is still readable). Default policy
is **block** on high severity — redaction is itself a form of data loss.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import List

PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "bearer_token": re.compile(r"(?i)bearer\s+[a-z0-9._\-]{20,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # capturing groups: 1 = key label, 2 = secret value (so we can redact only the value)
    "generic_secret": re.compile(
        r"(?i)\b(api[_-]?key|secret|password|passwd|token|client[_-]?secret)\b\s*[:=]\s*['\"]?([^\s'\"]{8,})"
    ),
    "internal_host": re.compile(r"\b[\w][\w.-]*\.(?:internal|corp|local|lbg|intranet)\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
}

# secret value lives in capturing group 2 for these (redact the value, keep label)
_VALUE_GROUP = {"generic_secret": 2}

_HIGH_ENTROPY = re.compile(r"['\"]([A-Za-z0-9+/=_\-]{24,})['\"]")

HIGH_SEVERITY = {"aws_access_key", "private_key", "github_token", "bearer_token", "slack_token", "jwt"}

REDACTION = "«REDACTED»"


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = {c: s.count(c) for c in set(s)}
    n = len(s)
    return -sum((k / n) * math.log2(k / n) for k in counts.values())


def _line_of(md: str, pos: int) -> int:
    return md.count("\n", 0, pos) + 1


def _mask(s: str) -> str:
    return s[:4] + "…" + s[-2:] if len(s) > 8 else "•••"


@dataclass
class Findings:
    items: List[dict] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return any(i["severity"] == "high" for i in self.items)

    @property
    def high(self) -> List[dict]:
        return [i for i in self.items if i["severity"] == "high"]

    def as_dict(self) -> dict:
        return {
            "count": len(self.items),
            "blocking": self.blocking,
            "items": self.items,
        }


def scan(md: str) -> Findings:
    md = md or ""
    f = Findings()
    seen: set[tuple] = set()
    for name, pat in PATTERNS.items():
        for m in pat.finditer(md):
            grp = _VALUE_GROUP.get(name, 0)
            raw = m.group(grp) if m.lastindex and grp <= (m.lastindex or 0) else m.group(0)
            key = (name, m.start(grp) if grp else m.start())
            if key in seen:
                continue
            seen.add(key)
            sev = "high" if name in HIGH_SEVERITY else "medium"
            f.items.append({
                "type": name,
                "match": _mask(raw),
                "severity": sev,
                "line": _line_of(md, m.start()),
            })
    for m in _HIGH_ENTROPY.finditer(md):
        val = m.group(1)
        if _entropy(val) >= 4.0:
            f.items.append({
                "type": "high_entropy_string",
                "match": _mask(val),
                "severity": "medium",
                "line": _line_of(md, m.start()),
            })
    f.items.sort(key=lambda i: (i["line"], i["type"]))
    return f


def redact(md: str) -> str:
    """Replace secret values with a marker, right-to-left to keep offsets valid.

    For ``generic_secret`` only the value is replaced (the ``API_KEY=`` label is
    kept so the document still reads sensibly).
    """
    md = md or ""
    spans: List[tuple[int, int]] = []
    for name, pat in PATTERNS.items():
        grp = _VALUE_GROUP.get(name, 0)
        for m in pat.finditer(md):
            spans.append((m.start(grp), m.end(grp)))
    for m in _HIGH_ENTROPY.finditer(md):
        if _entropy(m.group(1)) >= 4.0:
            spans.append((m.start(1), m.end(1)))
    out = md
    for start, end in sorted(spans, reverse=True):
        out = out[:start] + REDACTION + out[end:]
    return out
