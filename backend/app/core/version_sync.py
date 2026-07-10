"""Version/requirement sync check — no LLM, no network.

READMEs routinely say "requires Python 3.10+" or "Node 18+" in prose, and
that claim silently drifts from the manifest as the project's real minimum
version changes. This module extracts both sides — the claim in the README
text and the declared minimum in the project's manifest file(s) — and flags
a mismatch. Manifest content must be supplied by the caller (e.g. fetched
from the repo in the GitHub-integrated flow); this module does no I/O.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

# README prose claim, e.g. "Python 3.10+", "requires Node.js 18", "Go 1.21".
_CLAIM = re.compile(
    r"\b(Python|Node(?:\.js)?|Go(?:lang)?|Ruby|Java|PHP|Rust)\s+(?:version\s+)?v?(\d+(?:\.\d+){0,2})\+?",
    re.I,
)

_TOOL_ALIASES = {
    "python": "python",
    "node": "node",
    "node.js": "node",
    "go": "go",
    "golang": "go",
    "ruby": "ruby",
    "java": "java",
    "php": "php",
    "rust": "rust",
}

_VERSION_NUM = re.compile(r"\d+(?:\.\d+)+|\d+")


def _canon(tool: str) -> str:
    return _TOOL_ALIASES.get(tool.lower(), tool.lower())


def _first_version(s: str) -> Optional[str]:
    m = _VERSION_NUM.search(s)
    return m.group(0) if m else None


def extract_claims(md: str) -> List[dict]:
    out = []
    for m in _CLAIM.finditer(md or ""):
        out.append({"tool": _canon(m.group(1)), "version": m.group(2), "raw": m.group(0)})
    return out


def parse_manifest(filename: str, content: str) -> Dict[str, str]:
    """Best-effort minimum-version extraction, keyed by canonical tool name."""
    name = filename.lower()
    declared: Dict[str, str] = {}
    try:
        if name.endswith("pyproject.toml"):
            m = re.search(r'requires-python\s*=\s*"([^"]+)"', content)
            if m:
                v = _first_version(m.group(1))
                if v:
                    declared["python"] = v
        elif name.endswith("package.json"):
            data = json.loads(content)
            node = (data.get("engines") or {}).get("node")
            if node:
                v = _first_version(node)
                if v:
                    declared["node"] = v
        elif name.endswith("go.mod"):
            m = re.search(r"(?m)^go\s+(\d+\.\d+)", content)
            if m:
                declared["go"] = m.group(1)
        elif name.endswith("cargo.toml"):
            m = re.search(r'rust-version\s*=\s*"([^"]+)"', content)
            if m:
                v = _first_version(m.group(1))
                if v:
                    declared["rust"] = v
    except Exception:  # noqa: BLE001 — malformed manifest, just skip it
        pass
    return declared


def _parts(version: str) -> tuple:
    return tuple(int(p) for p in version.split(".") if p.isdigit())


def _conflicts(claim: str, manifest: str) -> bool:
    """A README claim is only as precise as it states — '18' matches '18.4.2'.

    Compare component-by-component up to the claim's own precision; only a
    genuine disagreement (not merely a claim that omits minor/patch) counts.
    """
    c, m = _parts(claim), _parts(manifest)
    return c[: len(m)] != m[: len(c)]


def check(md: str, manifests: Dict[str, str]) -> dict:
    declared: Dict[str, str] = {}
    for filename, content in (manifests or {}).items():
        declared.update(parse_manifest(filename, content))

    claims = extract_claims(md)
    mismatches = []
    for c in claims:
        manifest_version = declared.get(c["tool"])
        if manifest_version and _conflicts(c["version"], manifest_version):
            mismatches.append({
                **c,
                "manifest_version": manifest_version,
                "reason": f"README claims {c['tool']} {c['version']}, manifest declares {manifest_version}",
            })
    return {"checked": len(claims), "declared": declared, "mismatches": mismatches}
