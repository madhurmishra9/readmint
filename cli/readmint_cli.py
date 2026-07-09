#!/usr/bin/env python3
"""Readmint CLI — scriptable refinement and a pre-commit entrypoint.

A thin client over the Readmint API. Exit codes are CI-friendly:
  0  success
  2  secrets detected (blocked)
  3  content loss detected (not written)
  4  transport / API error
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import httpx
import typer

app = typer.Typer(add_completion=False, help="Refine README files via a Readmint server.")

DEFAULT_API = "http://localhost:8080"


def _post(api: str, path: str, **kwargs):
    try:
        r = httpx.post(f"{api.rstrip('/')}{path}", timeout=300, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        typer.secho(f"API error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(4)


def _get(api: str, path: str, **kwargs):
    try:
        r = httpx.get(f"{api.rstrip('/')}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        typer.secho(f"API error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(4)


@app.command()
def refine(
    path: str = typer.Argument(..., help="Path to a README/markdown file."),
    api: str = typer.Option(DEFAULT_API, envvar="READMINT_API"),
    write: bool = typer.Option(False, help="Overwrite the file in place when safe."),
    template: Optional[str] = typer.Option(None, help="Org template name."),
    check_links: bool = typer.Option(False, help="Validate links (network)."),
    check_style: bool = typer.Option(False, help="Run the deterministic prose/style lint."),
    redact: bool = typer.Option(False, help="Redact secrets instead of blocking."),
    allow_secrets: bool = typer.Option(False, help="Proceed despite high-severity secrets."),
    model: Optional[str] = typer.Option(None, help="LLM model id (e.g. a local model)."),
):
    """Refine a single file. With --write, only writes when verified & loss-free."""
    content = Path(path).read_text(encoding="utf-8")
    form = {
        "text": content,
        "check_links": str(check_links).lower(),
        "check_style": str(check_style).lower(),
        "redact": str(redact).lower(),
        "allow_secrets": str(allow_secrets).lower(),
    }
    if template:
        form["template"] = template
    if model:
        form["model"] = model
    data = _post(api, "/api/refine", data=form)

    if data.get("status") == "blocked":
        n = data.get("secrets", {}).get("count", "?")
        typer.secho(f"Secrets detected ({n}); aborting.", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)
    if data.get("loss"):
        typer.secho("Content loss detected; not writing.", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(3)

    if write:
        Path(path).write_text(data["markdown"], encoding="utf-8")
        before = data["score"]["before"]["score"]
        after = data["score"]["after"]["score"]
        typer.secho(f"Refined {path} (score {before} -> {after}).", fg=typer.colors.GREEN)
    else:
        sys.stdout.write(data["markdown"])

    style_report = data.get("style")
    if style_report and style_report.get("count"):
        typer.secho(f"\n{style_report['count']} style finding(s):", fg=typer.colors.YELLOW, err=True)
        for f in style_report["findings"][:20]:
            where = f"line {f['line']}" if f.get("line") else "doc"
            typer.echo(f"  [{f['rule']}] {where}: {f['message']}", err=True)


@app.command()
def score(
    path: str = typer.Argument(...),
    api: str = typer.Option(DEFAULT_API, envvar="READMINT_API"),
    template: Optional[str] = typer.Option(None),
):
    """Print the deterministic completeness score (no LLM call)."""
    content = Path(path).read_text(encoding="utf-8")
    payload = {"text": content}
    if template:
        payload["template"] = template
    data = _post(api, "/api/score", json=payload)
    typer.echo(f"score: {data['score']}/100 ({data['mode']})")
    for name, row in data["breakdown"].items():
        mark = "[x]" if row["passed"] else "[ ]"
        typer.echo(f"  {mark} {name} ({row['weight']})")


@app.command()
def lint(
    path: str = typer.Argument(...),
    api: str = typer.Option(DEFAULT_API, envvar="READMINT_API"),
):
    """Run the deterministic prose/style lint (no LLM call)."""
    content = Path(path).read_text(encoding="utf-8")
    data = _post(api, "/api/style", json={"text": content})
    if not data["count"]:
        typer.secho("No style findings.", fg=typer.colors.GREEN)
        return
    typer.secho(f"{data['count']} style finding(s):", fg=typer.colors.YELLOW)
    for f in data["findings"]:
        where = f"line {f['line']}" if f.get("line") else "doc"
        typer.echo(f"  [{f['rule']}] {where}: {f['message']}")
    raise typer.Exit(1)


@app.command()
def templates(
    api: str = typer.Option(DEFAULT_API, envvar="READMINT_API"),
    doc_type: Optional[str] = typer.Option(None, help="Filter to one doc type, e.g. 'contributing' or 'security'."),
):
    """List org template names (and doc types) available on the server."""
    data = _get(api, "/api/templates", params={"doc_type": doc_type} if doc_type else {})
    for name in data["templates"]:
        typer.echo(name)
    if not doc_type:
        typer.echo(f"\ndoc types: {', '.join(data['doc_types'])}", err=True)


if __name__ == "__main__":
    app()
