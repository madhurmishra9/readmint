"""Export refined Markdown — HTML, PDF, or a Confluence page.

HTML uses ``markdown-it-py``. PDF uses WeasyPrint, imported lazily because it
pulls heavy native libs that may be absent in minimal images. Confluence uses
the Cloud REST API (storage representation).
"""
from __future__ import annotations

from markdown_it import MarkdownIt

from ..config import settings

_md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("table")

_HTML_SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
   max-width:820px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#1b1f23}}
 pre{{background:#f6f8fa;padding:1rem;overflow:auto;border-radius:6px}}
 code{{background:#f6f8fa;padding:.15em .35em;border-radius:4px}}
 pre code{{background:none;padding:0}}
 h1,h2{{border-bottom:1px solid #eaecef;padding-bottom:.3em}}
 table{{border-collapse:collapse}} td,th{{border:1px solid #dfe2e5;padding:6px 13px}}
 img{{max-width:100%}}
</style></head><body>
{body}
</body></html>"""


def to_html(markdown: str, title: str = "README") -> str:
    return _HTML_SHELL.format(title=title, body=_md.render(markdown or ""))


def to_pdf(markdown: str, title: str = "README") -> bytes:
    try:
        from weasyprint import HTML  # lazy, heavy
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PDF export needs WeasyPrint and its system libraries") from e
    return HTML(string=to_html(markdown, title)).write_pdf()


def to_confluence(markdown: str, title: str, space: str | None = None, parent_id: str | None = None) -> dict:
    if not settings.confluence_enabled:
        raise RuntimeError("Confluence not configured (RF_CONFLUENCE_BASE_URL / TOKEN)")
    import httpx

    space_key = space or settings.confluence_space
    if not space_key:
        raise RuntimeError("no Confluence space key provided")
    body = {
        "spaceId": space_key,
        "status": "current",
        "title": title,
        "body": {"representation": "storage", "value": _md.render(markdown or "")},
    }
    if parent_id:
        body["parentId"] = parent_id
    with httpx.Client(
        base_url=settings.confluence_base_url.rstrip("/"),
        proxy=settings.https_proxy or None,
        verify=settings.ca_bundle_path or True,
        timeout=30.0,
        headers={"Authorization": f"Bearer {settings.confluence_token}", "Content-Type": "application/json"},
    ) as c:
        r = c.post("/wiki/api/v2/pages", json=body)
        r.raise_for_status()
        data = r.json()
    page_id = data.get("id")
    links = data.get("_links", {})
    base = links.get("base", settings.confluence_base_url.rstrip("/"))
    webui = links.get("webui", "")
    return {"id": page_id, "url": (base + webui) if webui else None, "title": title}
