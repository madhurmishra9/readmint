# Readmint

![status](https://img.shields.io/badge/status-active-success)
![python](https://img.shields.io/badge/python-3.12-blue)
![deploy](https://img.shields.io/badge/deploy-kubernetes-326ce5)
![license](https://img.shields.io/badge/license-internal-lightgrey)

> Mint fresh, well-structured READMEs — at scale, without losing a single line.

Readmint ingests one README or thousands, refines them with a Cortex-hosted LLM, and **guarantees no content is lost** by verifying every code block, inline command, URL, image reference, version number, and email survives the rewrite. It scores documentation, enforces org templates, scans for secrets before anything leaves your network, and ships results as a download, a GitHub PR, or a Confluence page.

## Table of Contents

- [Why Readmint](#why-readmint)
- [Features](#features)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deployment](#deployment)
- [Development](#development)
- [Roadmap](#roadmap)
- [License](#license)

## Why Readmint

Most LLM "beautifier" tools quietly drop commands, links, and config values while reformatting. In a regulated environment that is unacceptable. Readmint treats the model as a **proposer** and adds a deterministic **verifier**: any refinement that loses content is rejected and retried, and the user always sees a diff and a content-preservation report before accepting. Prose and headings may be reorganized freely; data-bearing atoms may not vanish.

## Features

- **Lossless refinement** — deterministic content-preservation guard; output rejected/retried on any loss, with residual loss reported rather than shipped.
- **Batch processing** — refine a zip or a list of documents with a bounded worker pool.
- **GitHub-native** — pull a README from `owner/repo@ref` and open a PR (always on a new branch, never the default).
- **Secret & PII gate** — scans for keys, tokens, internal hostnames, and emails *before* any data reaches the LLM.
- **Documentation scoring** — deterministic completeness score, before and after.
- **Template enforcement** — map content into org-standard section structures.
- **Link validation** — flags dead URLs.
- **Deterministic ToC** — correct GitHub anchors, computed not guessed.
- **Change summary** — concise, model-generated "what changed".
- **Multiple surfaces** — web UI, CLI, pre-commit hook, and REST API.
- **Export** — download `.md`, HTML, or PDF, or push to Confluence.
- **Enterprise-ready** — Azure AD SSO (oauth2-proxy), RBAC, audit log, Prometheus metrics, token-cost caching.

## How It Works

```
secrets_scan -> score(before) -> inventory(before) -> LLM refine
            -> verify / retry on loss -> ToC -> link check
            -> score(after) -> change summary -> diff + reports
```

The LLM may reorder, re-level, and reword freely. It may **not** drop a code block, inline command, URL, image, version number, or email — and that constraint is enforced in code (`core/inventory.py`), not by trust. The secret scan runs **before** any call to the LLM.

## Quick Start

### Run with Docker

```bash
docker build -t readmint:local .

# Stub mode (no external LLM) — runs immediately, refines deterministically
# while preserving all content. Great for a first look and for CI.
docker run -p 8080:8080 readmint:local

# Live Cortex LLM (OAuth2 client-credentials):
docker run -p 8080:8080 \
  -e RF_LLM_STUB=false \
  -e RF_LLM_BASE_URL="https://cortex.internal.example/v1" \
  -e RF_LLM_TOKEN_URL="https://login.internal.example/oauth2/token" \
  -e RF_LLM_CLIENT_ID="$RF_LLM_CLIENT_ID" \
  -e RF_LLM_CLIENT_SECRET="$RF_LLM_CLIENT_SECRET" \
  readmint:local
```

Open http://localhost:8080, paste or attach a README, and refine. The API is at http://localhost:8080/docs.

## Configuration

All settings are environment variables prefixed `RF_`. With no LLM variables set, the app runs in **stub mode** (`RF_LLM_BASE_URL` empty ⇒ no network call), so it is usable out of the box.

| Variable | Required | Default | Description |
|---|---|---|---|
| `RF_LLM_STUB` | no | `false` | Force stub mode (also implied when `RF_LLM_BASE_URL` is empty) |
| `RF_LLM_BASE_URL` | for live LLM | — | Cortex API base URL (OpenAI-compatible `/chat/completions`) |
| `RF_LLM_TOKEN_URL` | for live LLM | — | OAuth2 client-credentials token endpoint |
| `RF_LLM_CLIENT_ID` | for live LLM | — | OAuth2 client id |
| `RF_LLM_CLIENT_SECRET` | for live LLM | — | OAuth2 client secret |
| `RF_LLM_SCOPE` | no | — | OAuth2 scope |
| `RF_LLM_MODEL` | no | `cortex-default` | Model identifier |
| `RF_MAX_RETRIES` | no | `2` | Loss-repair retries before reporting residual loss |
| `RF_SECRET_POLICY` | no | `block` | `block` or `redact` high-severity findings |
| `RF_HTTPS_PROXY` | no | — | Corporate egress proxy (honoured by every outbound call) |
| `RF_CA_BUNDLE_PATH` | no | — | Custom CA bundle for TLS |
| `RF_BATCH_CONCURRENCY` | no | `4` | Max parallel refinements |
| `RF_REDIS_URL` | no | — | Enables token-cost caching |
| `RF_DATABASE_URL` | no | — | Enables history/audit |
| `RF_GH_APP_ID` / `RF_GH_INSTALLATION_ID` / `RF_GH_PRIVATE_KEY` | no | — | GitHub App (PR flow) |
| `RF_CONFLUENCE_BASE_URL` / `RF_CONFLUENCE_TOKEN` | no | — | Confluence export |
| `RF_AUTH_ENABLED` | no | `false` | Trust oauth2-proxy identity headers (RBAC) |

## Usage

### Web UI

Paste text, attach a `.md` file, or upload a zip. Review the score change, the diff, and the loss/secret reports, then download or open a PR.

### CLI

```bash
python cli/readmint_cli.py refine README.md --write --check-links
python cli/readmint_cli.py score README.md --template service
```

Exit codes: `0` success, `2` secrets detected, `3` content loss detected, `4` transport/API error — safe to wire into CI.

### Pre-commit hook

```yaml
repos:
  - repo: local
    hooks:
      - id: readmint
        name: Readmint README refine
        entry: python cli/readmint_cli.py refine --write
        language: python
        additional_dependencies: ["typer>=0.12", "httpx>=0.27"]
        files: README\.md$
```

A ready-made hook is also published in `.pre-commit-hooks.yaml`.

### API

```bash
curl -X POST http://localhost:8080/api/refine \
  -F "file=@README.md" -F "check_links=true"
```

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/refine` | Single README (paste/attach), full pipeline |
| POST | `/api/batch` · `/api/batch/zip` | Many → results table |
| POST | `/api/github/refine` | `{owner, repo, ref}` → refined + optional PR |
| POST | `/api/score` | Score only, no LLM call |
| POST | `/api/export` | HTML / PDF, or push to Confluence |
| GET | `/api/templates` · `/api/history` | Templates · audit runs |
| GET | `/metrics` · `/healthz` | Prometheus · liveness/readiness |

## Deployment

Apply the manifests in `deploy/`:

```bash
kubectl apply -f deploy/configmap.yaml
kubectl apply -f deploy/secret.yaml        # from secret.example.yaml
kubectl apply -f deploy/deployment.yaml
kubectl apply -f deploy/service.yaml
kubectl apply -f deploy/ingress.yaml
kubectl apply -f deploy/hpa.yaml
```

Optional add-ons (`postgres.yaml`, `redis.yaml`) enable history/audit and caching. SSO is provided by an oauth2-proxy sidecar in the Deployment. All outbound traffic honours the configured proxy and CA bundle. CI/CD is described in `harness-pipeline.yaml`.

## Development

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# frontend
cd frontend && npm install && npm run dev

# tests
cd backend && RF_LLM_STUB=true pytest -q
```

Build order follows the phased roadmap: the content-preservation guard and the secret gate are implemented and tested **before** the LLM is wired in.

## Roadmap

- [x] Lossless single-file refinement
- [x] Secret/PII gate
- [x] Documentation scoring
- [x] Batch + GitHub PR flow
- [x] Templates & governance scoring
- [x] CLI + pre-commit
- [x] Export (HTML/PDF/Confluence)
- [x] SSO, RBAC, audit, observability
- [ ] Section-level accept/reject in the diff viewer
- [ ] Validation against a live Cortex endpoint (stub-backed by default today)

## License

Internal — see your organization's licensing policy.
