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
from .core import inventory, scoring, secrets_scan, terminology, toc
from .cortex_client import cortex
from .observability import (LLM_RETRIES, PIPELINE_LATENCY, PIPELINE_RUNS, SECRETS_BLOCKED)

log = structlog.get_logger(__name__)


def _template_name(template: Optional[dict]) -> str:
    return (template or {}).get("name", "") if template else ""


@PIPELINE_LATENCY.time()
def run_pipeline(document: str, *, template: Optional[dict] = None, opts: Optional[dict] = None) -> dict:
    opts = opts or {}

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
    output = cortex.complete(system, prompts.USER.format(document=sanitized), model=model)

    # 5. verify / retry on any content loss
    retries = 0
    report = inventory.diff(before_inv, inventory.extract(output))
    while inventory.has_loss(report) and retries < settings.max_retries:
        retries += 1
        log.info("pipeline.repair_retry", attempt=retries)
        output = cortex.complete(system, prompts.repair(report, output), model=model)
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
        "summary": change_summary,
        "retries": retries,
        "cached": False,
    }

    if use_cache:
        from .services import cache
        cache.put(document, _template_name(template), result, ttl=settings.cache_ttl)
    return result
