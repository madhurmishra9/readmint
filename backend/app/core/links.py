"""Dead-link check. Routed through the corporate proxy / CA bundle like Cortex."""
from __future__ import annotations

import httpx

from ..config import settings
from .inventory import extract


def validate(md: str, timeout: float = 8.0) -> dict:
    inv = extract(md)
    # Check both link targets *and* image/badge URLs (shields.io badges, screenshots).
    urls = sorted(
        {u for u in inv.urls if u.startswith("http")}
        | {u for u in inv.images if u.startswith("http")}
    )
    results = []
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout,
        proxy=settings.https_proxy or None,
        verify=settings.ca_bundle_path or True,
        headers={"User-Agent": "Readmint-linkcheck/0.1"},
    ) as c:
        for url in urls:
            try:
                r = c.head(url)
                if r.status_code >= 400:  # HEAD blocked/unsupported → confirm with GET
                    r = c.get(url)
                results.append({"url": url, "status": r.status_code, "ok": r.status_code < 400})
            except Exception as e:  # noqa: BLE001 — report, never raise
                results.append({"url": url, "status": None, "ok": False, "error": type(e).__name__})
    return {"checked": len(results), "broken": [r for r in results if not r["ok"]]}
