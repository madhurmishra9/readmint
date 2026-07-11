"""The one ordered pipeline. The LLM proposes; the deterministic verifier disposes.

Order (do not reorder — see copilot-instructions):
    secrets_scan -> score(before) -> inventory(before) -> LLM -> verify/retry
    -> toc -> links -> score(after) -> summary
"""
from __future__ import annotations

from typing import Optional

import structlog

from . import prompts
from .config import settings
from .core import badges, drift, inventory, scoring, secrets_scan, style, terminology, toc, version_sync
from .cortex_client import cortex
from .observability import (LLM_RETRIES, PIPELINE_LATENCY, PIPELINE_RUNS, SECRETS_BLOCKED)

log = structlog.get_logger(__name__)


def _template_name(template: Optional[dict]) -> str:
    return (template or {}).get("name", "") if template else ""


def _normalize_newlines(text: str) -> str:
    """CRLF/CR -> LF. Browser multipart form submission (and Windows-authored
    files) routinely carry CRLF; every downstream regex — heading detection,
    ToC anchors, the JS section splitter — assumes LF, so normalise once here
    rather than let \\r leak into every line and corrupt line-exact matching."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


@PIPELINE_LATENCY.time()
def run_pipeline(document: str, *, template: Optional[dict] = None, opts: Optional[dict] = None) -> dict:
    opts = opts or {}
    document = _normalize_newlines(document)

    # 0. cache (optional) — keyed on sanitised intent: document + template
    use_cache = opts.get("use_cache", True) and settings.cache_enabled
    if use_cache:
        from .services import cache
        hit = cache.get(document, _template_name(template))
        if hit is not None:
            log.info("pipeline.cache_hit")
            return {**hit, "cached": True}

    # 1. egress gate — BEFORE any network call to Cortex
    findings = secrets_scan.scan(document)
    do_redact = bool(opts.get("redact")) or settings.secret_policy == "redact"
    if findings.blocking and not opts.get("allow_secrets") and not do_redact:
        log.warning("pipeline.blocked_on_secrets", count=len(findings.high))
        SECRETS_BLOCKED.inc()
        PIPELINE_RUNS.labels(status="blocked", verified="na").inc()
        return {"status": "blocked", "secrets": findings.as_dict()}

    document = terminology.normalize(document, opts.get("glossary")) if opts.get("glossary") else document
    sanitized = secrets_scan.redact(document) if do_redact else document

    # 2/3. deterministic baseline
    score_before = scoring.score(sanitized, template)
    before_inv = inventory.extract(sanitized)

    # 4. LLM refine
    model = opts.get("model") or None
    system = prompts.system_for(template)
    output = _normalize_newlines(cortex.complete(system, prompts.USER.format(document=sanitized), model=model))

    # 5. verify / retry on any content loss
    retries = 0
    report = inventory.diff(before_inv, inventory.extract(output))
    while inventory.has_loss(report) and retries < settings.max_retries:
        retries += 1
        log.info("pipeline.repair_retry", attempt=retries)
        output = _normalize_newlines(cortex.complete(system, prompts.repair(report, output), model=model))
        report = inventory.diff(before_inv, inventory.extract(output))

    # 6. deterministic ToC + anchors
    output = toc.ensure(output)

    # 7. optional dead-link check
    link_report = None
    if opts.get("check_links"):
        from .core import links
        link_report = links.validate(output)

    # 8. after-score + optional change summary
    score_after = scoring.score(output, template)
    change_summary = None
    if opts.get("summary"):
        from .core import summary
        change_summary = summary.summarize(sanitized, output)

    # 9. optional prose/style lint (deterministic, advisory — not part of the score)
    style_report = style.lint(output) if opts.get("check_style") else None

    # 10. optional badge staleness check (no repo access needed; ground truth is optional)
    badges_report = None
    if opts.get("check_badges"):
        badges_report = badges.validate(
            output,
            expected_license=opts.get("expected_license"),
            expected_version=opts.get("expected_version"),
        )

    # 11. optional doc-drift check — only meaningful with repo context (populated
    # by the GitHub-integrated flow; absent for a bare paste/upload)
    drift_report = None
    if opts.get("check_drift") and opts.get("repo_files") is not None:
        drift_report = drift.check(output, opts["repo_files"])

    # 12. optional version-sync check — only meaningful with manifest context
    # (populated by the GitHub-integrated flow; absent for a bare paste/upload)
    version_sync_report = None
    if opts.get("check_version_sync") and opts.get("manifests") is not None:
        version_sync_report = version_sync.check(output, opts["manifests"])

    final = inventory.diff(before_inv, inventory.extract(output))
    verified = not inventory.has_loss(final)
    if retries:
        LLM_RETRIES.inc(retries)
    PIPELINE_RUNS.labels(status="ok", verified=str(verified).lower()).inc()
    if not verified:
        log.warning("pipeline.residual_loss", loss={k: len(v) for k, v in final.items() if v})

    result = {
        "status": "ok",
        "markdown": output,
        "verified": verified,
        "loss": {k: v for k, v in final.items() if v} or None,
        "secrets": findings.as_dict(),
        "redacted": do_redact,
        "score": {"before": score_before, "after": score_after},
        "links": link_report,
        "style": style_report,
        "badges": badges_report,
        "drift": drift_report,
        "version_sync": version_sync_report,
        "summary": change_summary,
        "retries": retries,
        "cached": False,
    }

    if use_cache:
        from .services import cache
        cache.put(document, _template_name(template), result, ttl=settings.cache_ttl)
    return result
