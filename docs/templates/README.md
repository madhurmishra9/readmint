# Template Library

Readmint ships a library of org templates in `backend/templates/*.yaml`. Each
template is a contract: a `name`, a `description`, and an ordered list of
`sections` marked `required: true|false`. When a template is selected (via
`--template <name>` in the CLI, `POST /api/refine` with a `template` field,
or the template dropdown in the UI), Readmint:

- reshapes the LLM system prompt so generated/refined content maps onto the
  template's sections, and
- scores the resulting README against that section list instead of the
  generic rubric (`GET/POST` scoring endpoints, `app/core/scoring.py`).

Run `readmint templates` (or `GET /api/templates`) to list the template names
available at runtime — the list is read from `backend/templates/` at
startup, so dropping a new `*.yaml` file there is enough to register it.

## Available templates

| Template file | Name | Use for |
|---|---|---|
| `service.yaml` | Internal Service | A deployable internal service (existing) |
| `library.yaml` | Shared Library | A reusable library / SDK (existing) |
| `terraform-module.yaml` | Terraform Module | A Terraform module (existing) |
| [`cli-tool.yaml`](cli-tool.md) | CLI Tool | A command-line tool / utility |
| [`web-app.yaml`](web-app.md) | Web Application | A frontend / full-stack web app |
| [`rest-api.yaml`](rest-api.md) | REST API | A public/consumer-facing HTTP API |
| [`mobile-app.yaml`](mobile-app.md) | Mobile App | An iOS/Android application |
| [`ml-project.yaml`](ml-project.md) | Machine Learning Project | A model training/experiment repo |
| [`npm-package.yaml`](npm-package.md) | NPM Package | A published JS/TS package |
| [`python-package.yaml`](python-package.md) | Python Package | A PyPI-published package |
| [`docker-image.yaml`](docker-image.md) | Docker Image | A published container image |
| [`github-action.yaml`](github-action.md) | GitHub Action | A reusable GitHub Action |
| [`vscode-extension.yaml`](vscode-extension.md) | VS Code Extension | A VS Code Marketplace extension |
| [`browser-extension.yaml`](browser-extension.md) | Browser Extension | A Chrome/Firefox/Edge extension |
| [`helm-chart.yaml`](helm-chart.md) | Helm Chart | A Kubernetes Helm chart |
| [`monorepo.yaml`](monorepo.md) | Monorepo | A multi-package/service monorepo |

Each linked page shows the template's required/optional sections and a short
worked example of a README that satisfies it, so you can see what a passing
score actually looks like before you point Readmint at your own repo.

## Adding your own template

Drop a new `*.yaml` file into `backend/templates/` with the same shape:

```yaml
name: My Template
description: One-line description of what this contract is for.
sections:
  - { heading: Overview, required: true }
  - { heading: Some Optional Section, required: false }
```

`app/core/templates.py` validates and caches the file the first time it's
loaded — no code changes or restarts of the template registry are required
beyond adding the file (a process restart picks up new files since the list
is read from disk on each `list_templates()` call, but individual loads are
cached with `lru_cache`).
