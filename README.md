# 🌿 Readmint

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
- **GitHub-native** — pull a README from `owner/repo@ref` and open a PR (always on a new branch, never the default). Authenticate with your own **Personal Access Token** (bring-your-own, per request) or a deployment-wide GitHub App.
- **Secret & PII gate** — scans for keys, tokens, internal hostnames, and emails *before* any data reaches the LLM.
- **Documentation scoring** — deterministic completeness score, before and after.
- **Template enforcement** — map content into org-standard section structures. 16 built-in templates (CLI tool, web app, REST API, mobile app, ML project, npm/Python package, Docker image, GitHub Action, VS Code/browser extension, Helm chart, monorepo, plus the original service/library/Terraform-module) — see [`docs/templates`](docs/templates/README.md) for the full list and worked examples.
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

### One-click deploy

The fastest way to get a running instance. **Prerequisite:** [Docker](https://docs.docker.com/get-docker/) installed and running. From the repo root:

```bash
./deploy.sh              # macOS / Linux
```
```powershell
.\deploy.ps1             # Windows
```

The script builds the image, replaces any previous `readmint` container, starts it, waits for `/healthz`, prints the URL, and opens your browser at http://localhost:8080. If the container never goes healthy, it prints the logs.

**Options**

| | macOS / Linux | Windows |
|---|---|---|
| Change the host port | `PORT=9000 ./deploy.sh` | `.\deploy.ps1 -Port 9000` |
| Live LLM / other config | put `RF_*` vars in a root `.env` | put `RF_*` vars in a root `.env` |

A root `.env`, if present, is passed straight into the container (`--env-file`). With none, the app runs in **stub mode** — no external LLM, fully functional, content-preserving.

> Windows: if you see *"running scripts is disabled on this system"*, launch once with
> `powershell -ExecutionPolicy Bypass -File .\deploy.ps1`.

To tear down: `docker rm -f readmint`.

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

## LLM providers

Readmint resolves a provider on every call, in this order:

1. **Stub** — when `RF_LLM_STUB=true`. No network; a deterministic identity refine that still preserves every atom. Used by tests/CI.
2. **Cortex** — when `RF_LLM_BASE_URL` is set. The hosted LLM (OAuth2 client-credentials).
3. **Local** — the default when Cortex isn't configured: any OpenAI-compatible server reachable at `RF_LOCAL_LLM_BASE_URL` (**Ollama** by default, also LM Studio / vLLM). If nothing is reachable, Readmint falls back to the stub, so it always runs.

So with **no configuration at all**, Readmint uses your **local LLM if one is running**, and the stub otherwise. The active provider and the model in use are shown in the UI; when a local server is detected, a **model selector** lets you pick among the models it reports. Reasoning ("thinking") models are supported — their `<think>…</think>` scratchpad is stripped from every completion so it never reaches the README or the no-loss verifier.

```bash
# Use a local Ollama model (after `ollama pull qwen3`):
ollama serve &                       # exposes http://localhost:11434
RF_LOCAL_LLM_MODEL=qwen3 uvicorn app.main:app --port 8080
```

> Running in Docker? `localhost` is the container, not your host. The one-click `deploy.sh` / `deploy.ps1` already wire `host.docker.internal` so a host Ollama is reached automatically; otherwise set `RF_LOCAL_LLM_BASE_URL=http://host.docker.internal:11434/v1`.

## Configuration

All settings are environment variables prefixed `RF_`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `RF_LLM_STUB` | no | `false` | Force stub mode (no LLM call) |
| `RF_LLM_BASE_URL` | for Cortex | — | Cortex API base URL (OpenAI-compatible `/chat/completions`) |
| `RF_LLM_TOKEN_URL` | for Cortex | — | OAuth2 client-credentials token endpoint |
| `RF_LLM_CLIENT_ID` | for Cortex | — | OAuth2 client id |
| `RF_LLM_CLIENT_SECRET` | for Cortex | — | OAuth2 client secret |
| `RF_LLM_SCOPE` | no | — | OAuth2 scope |
| `RF_LLM_MODEL` | no | `cortex-default` | Cortex model identifier |
| `RF_LOCAL_LLM_BASE_URL` | no | `http://localhost:11434/v1` | Local OpenAI-compatible server (Ollama/LM Studio/vLLM) |
| `RF_LOCAL_LLM_MODEL` | no | — | Pinned local model (empty ⇒ first the server reports) |
| `RF_LOCAL_LLM_TIMEOUT` | no | `600` | Per-call timeout for local models (seconds) |
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

### GitHub (bring your own PAT)

Open the **GitHub** tab in the web UI, paste a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope, enter `owner` / `repo`, and refine. Readmint fetches the live README with your token, runs the full no-loss pipeline, then — if "open a PR" is checked — commits the refined README on a **new branch** and opens a pull request. The token is used only for that request and is never stored.

The same flow is available over the API:

```bash
curl -X POST http://localhost:8080/api/github/refine \
  -H "Content-Type: application/json" \
  -d '{"owner":"acme","repo":"widgets","open_pr":true,"pat":"ghp_xxx"}'
```

`pat` is optional: omit it and the request falls back to the configured GitHub App (`RF_GH_*`). The PR always targets the repo's default branch unless you pass `base`.

### CLI

```bash
python cli/readmint_cli.py refine README.md --write --check-links
python cli/readmint_cli.py score README.md --template service
```

Run `readmint templates` (or `GET /api/templates`) to list all available template names — see [`docs/templates`](docs/templates/README.md) for what each one expects.

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
