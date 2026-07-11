# Template Library

Readmint ships a library of org templates in `backend/templates/*.yaml`. Each
template is a contract: a `name`, a `description`, and an ordered list of
`sections` marked `required: true|false`. When a template is selected (via
`--template <name>` in the CLI, `POST /api/refine` with a `template` field,
or the template dropdown in the UI), Readmint:

- reshapes the LLM system prompt so generated/refined content maps onto the
  template's sections, and
- scores the resulting document against that section list instead of the
  generic rubric (`GET/POST` scoring endpoints, `app/core/scoring.py`).

Run `readmint templates` (or `GET /api/templates`) to list the template names
available at runtime — the list is read from `backend/templates/` at
startup, so dropping a new `*.yaml` file there is enough to register it.

Every template also carries a `doc_type` (`readme` by default). Pass
`?doc_type=contributing` to `GET /api/templates` (or `--doc-type contributing`
to `readmint templates`) to list only that kind — the same section-contract +
template-mode-scoring machinery applies to companion docs, not just
`README.md`.

## README templates

| Template file | Name | Use for |
|---|---|---|
| `service.yaml` | Internal Service | A deployable internal service |
| `library.yaml` | Shared Library | A reusable library / SDK |
| `terraform-module.yaml` | Terraform Module | A Terraform module |

## Companion doc templates

The same governance contract works for a repo's other standard docs, not
just `README.md` — pick a `doc_type` and the file it targets:

| Template file | `doc_type` | Targets |
|---|---|---|
| [`contributing.yaml`](contributing.md) | `contributing` | `CONTRIBUTING.md` |
| [`security.yaml`](security.md) | `security` | `SECURITY.md` |
| [`code-of-conduct.yaml`](code-of-conduct.md) | `code_of_conduct` | `CODE_OF_CONDUCT.md` |

Point Readmint's CLI/API at the companion file itself (e.g. `readmint refine
CONTRIBUTING.md --template contributing`) — the pipeline doesn't care what
the source file is named, only which template you select.

## Adding your own template

Drop a new `*.yaml` file into `backend/templates/` with the same shape:

```yaml
name: My Template
doc_type: readme  # optional — defaults to "readme"; use e.g. "contributing" for a companion doc
description: One-line description of what this contract is for.
sections:
  - { heading: Overview, required: true }
  - { heading: Some Optional Section, required: false }
```

`app/core/templates.py` validates and caches the file the first time it's
loaded — no code changes are required beyond adding the file.
