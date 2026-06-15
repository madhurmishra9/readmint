# 🌿 Readmint

Refine one README or thousands with a Cortex-hosted LLM **without losing any
data**. Readmint scores documents against a rubric, enforces org templates,
scans for secrets before anything leaves the cluster, and ships the result as a
download, a GitHub PR, or a Confluence page — from a browser, a CLI, a
pre-commit hook, or the API.

> **The spine:** the LLM proposes, a deterministic verifier disposes. Prose may
> be rewritten freely; code, URLs, versions, images and emails must survive, or
> the pipeline retries and reports residual loss — it never silently ships it.

## Pipeline

```
secrets_scan → score(before) → inventory(before) → LLM → verify/retry
            → toc → links → score(after) → summary
```

`secrets_scan` runs **before** any call to Cortex. High-severity findings block
by default (redaction is opt-in and treated as data loss).

## Quick start (local, stub LLM)

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate    # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                                 # RF_LLM_STUB=true by default
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080/docs for the API, or run the frontend dev server:

```bash
cd frontend && npm install && npm run dev            # proxies /api to :8080
```

Point at a real Cortex endpoint by setting `RF_LLM_STUB=false` and the
`RF_LLM_BASE_URL` / `RF_LLM_TOKEN_URL` / `RF_LLM_CLIENT_ID` / `RF_LLM_CLIENT_SECRET`
variables.

## CLI & pre-commit

```bash
python cli/readmint_cli.py refine README.md --write
python cli/readmint_cli.py score README.md --template service
```

`.pre-commit-hooks.yaml` exposes the `readmint` hook (refine + block on secrets
or content loss) for consumer repos.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/refine` | Single README (paste/attach), full pipeline |
| POST | `/api/batch` · `/api/batch/zip` | Many → results table |
| POST | `/api/github/refine` | `{owner,repo,ref}` → refined + optional PR |
| POST | `/api/score` | Score only, no LLM call |
| POST | `/api/export` | HTML / PDF, or push to Confluence |
| GET | `/api/templates` · `/api/history` | Templates · audit runs |
| GET | `/metrics` · `/healthz` | Prometheus · liveness/readiness |

## Add-ons (all optional, gated by env)

Redis cache (`RF_REDIS_URL`), Postgres history/audit (`RF_DATABASE_URL`),
GitHub App (`RF_GH_*`), Confluence (`RF_CONFLUENCE_*`), oauth2-proxy/Azure AD
(`RF_AUTH_ENABLED`). Unset → the feature is disabled and the core single
container still runs.

## Tests

```bash
cd backend && RF_LLM_STUB=true pytest -q
```

## Deploy

Multi-stage `Dockerfile` builds the frontend and bakes it into the backend
image (served at `/`). Kubernetes manifests live in `deploy/` (Deployment with
oauth2-proxy sidecar, Service, Ingress, HPA, optional Postgres/Redis). CI/CD in
`harness-pipeline.yaml`.

## Layout

```
backend/   FastAPI app, core/ (loss guard, secrets, scoring, toc, links, …),
           services/ (batch, github, export, cache, history), routers/, tests/
cli/       typer CLI + pre-commit entrypoint
frontend/  React + Vite (input, diff, score, loss/secret reports, export)
deploy/    Kubernetes manifests
```

See [Readmint-Implementation-Plan.md](Readmint-Implementation-Plan.md) for the
full design and phased roadmap.
