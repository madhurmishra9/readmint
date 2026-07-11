"""Badge staleness check — no network call (liveness is already covered by
``core/links.py``, which HEAD/GETs every image URL including badges).

This module instead looks *inside* a shields.io "static" badge URL — the kind
that bakes a literal value into the URL, e.g.
``https://img.shields.io/badge/license-MIT-blue`` — and flags it when the
baked-in value disagrees with ground truth supplied by the caller (the repo's
real license, the package's real version). Dynamic badges such as
``https://img.shields.io/github/license/<owner>/<repo>`` or
``https://img.shields.io/npm/v/<pkg>`` compute their own value on every render
and can never go stale, so they are reported but never flagged.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

_BADGE_IMG = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")
_SHIELDS_HOST = "img.shields.io"
_STATIC_PATH = re.compile(r"^/badge/(.+?)(?:\.svg|\.png)?$")
_DASH_ESCAPE = "\x00DASH\x00"


def _parse_static_path(path: str) -> Optional[Tuple[str, str, Optional[str]]]:
    m = _STATIC_PATH.match(path)
    if not m:
        return None
    # shields.io escapes a literal '-' as '--' and a literal '_' as '__'
    body = m.group(1).replace("--", _DASH_ESCAPE)
    parts = [p.replace(_DASH_ESCAPE, "-").replace("_", " ") for p in body.split("-")]
    if len(parts) < 2:
        return None
    label, message = parts[0], parts[1]
    color = parts[2] if len(parts) > 2 else None
    return label, message, color


def _badge_fields(url: str) -> Optional[Tuple[str, str]]:
    """(label, message) for a *static* shields.io badge, or None for a dynamic one."""
    parsed = urlparse(url)
    if _SHIELDS_HOST not in parsed.netloc:
        return None
    if parsed.path.startswith("/badge/"):
        parsed_badge = _parse_static_path(parsed.path)
        return (parsed_badge[0], parsed_badge[1]) if parsed_badge else None
    if parsed.path.startswith("/static/v1"):
        qs = parse_qs(parsed.query)
        label = (qs.get("label") or [None])[0]
        message = (qs.get("message") or [None])[0]
        return (label, message) if label and message else None
    return None


def _norm_version(v: str) -> str:
    return v.strip().lstrip("vV")


def extract(md: str) -> List[dict]:
    """Every shields.io badge referenced in the doc, static or dynamic."""
    out = []
    for m in _BADGE_IMG.finditer(md):
        alt, url = m.group(1), m.group(2)
        if _SHIELDS_HOST not in urlparse(url).netloc:
            continue
        out.append({"alt": alt, "url": url})
    return out


def validate(md: str, *, expected_license: Optional[str] = None, expected_version: Optional[str] = None) -> dict:
    badges = extract(md)
    stale = []
    for b in badges:
        fields = _badge_fields(b["url"])
        if not fields:
            continue  # dynamic badge, or an unrecognised shields.io URL shape
        label, message = fields
        b["label"], b["message"] = label, message
        ll = label.lower()
        if expected_license and "licen" in ll and message.lower() != expected_license.lower():
            stale.append({**b, "reason": f"badge says '{message}', repository license is '{expected_license}'"})
        elif expected_version and "version" in ll and _norm_version(message) != _norm_version(expected_version):
            stale.append({**b, "reason": f"badge says '{message}', current version is '{expected_version}'"})
    return {"checked": len(badges), "badges": badges, "stale": stale}
