# Readmint — Copilot / agent instructions

Readmint refines READMEs with an LLM but is governed by a deterministic
verifier: **the LLM proposes, the verifier disposes.** Keep that spine intact.

## Pipeline order (do not reorder)
```
secrets_scan -> score(before) -> inventory(before) -> LLM -> verify/retry
-> toc -> links -> score(after) -> summary
```

## Hard rules
- `secrets_scan` runs before ANY network call to Cortex. High-severity findings
  block by default; redaction is opt-in and treated as data loss.
- The no-loss guard (`core/inventory.py`) is authoritative. Prose may be
  rewritten freely; data atoms (code, URLs, images, numbers, emails) must
  survive. If they don't, the pipeline retries, then reports residual loss —
  it never silently ships loss.
- ToC anchors are computed deterministically in `core/toc.py`, never by the LLM.
- `services/github.py` only ever opens a PR on a new `readmint/*` branch; it
  never pushes to the default branch.
- All outbound HTTP (Cortex, GitHub, link-check, Confluence) honours
  `https_proxy` and `ca_bundle_path` from config.
- Feature add-ons (Redis, Postgres, oauth2-proxy, GitHub App, Confluence) must
  degrade gracefully when their env vars are absent. Gate on the
  `settings.*_enabled` properties.
- Never log README bodies or raw secret matches — masked types and counts only.

## Tests
- Every deterministic module has unit tests under `backend/tests/`.
- The pipeline is exercised in stub-LLM mode (`RF_LLM_STUB=true`); inject
  adversarial behaviour with `cortex.set_stub_responder(...)`.

## Suggested agent sequence
Follow the phase order in the implementation plan (§11). The loss guard and the
secret gate ship before anything touches the LLM.

## Claude split
Use Copilot for the deterministic modules and YAML; bring in Claude to
red-team `secrets_scan.py` / `inventory.py` with adversarial READMEs, tune the
template-aware system prompt, and review the GitHub App token/branch logic.
