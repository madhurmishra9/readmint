# Template: Monorepo

`backend/templates/monorepo.yaml` — for a monorepo housing multiple
packages or services.

| Section | Required |
|---|---|
| Overview | yes |
| Repository Structure | yes |
| Getting Started | yes |
| Workspaces | yes |
| Running Tests | no |
| Contributing | no |
| License | no |

## Example README that passes this template

```markdown
# platform

Monorepo for the platform team: the public API, the admin dashboard, and
shared internal packages.

## Overview

This repo hosts everything the platform team ships, managed as npm/PNPM
workspaces so shared code changes atomically with the services that use
it.

## Repository Structure

    apps/
      api/         REST API service
      dashboard/   Admin dashboard (React)
    packages/
      auth/        Shared auth middleware
      ui/          Shared React component library

## Getting Started

    git clone https://github.com/example/platform.git
    cd platform
    pnpm install
    pnpm dev

`pnpm dev` runs `api` and `dashboard` together via Turborepo, with `auth`
and `ui` linked as local workspace packages.

## Workspaces

| Workspace | Path | Description |
|---|---|---|
| `@platform/api` | `apps/api` | REST API service |
| `@platform/dashboard` | `apps/dashboard` | Admin dashboard |
| `@platform/auth` | `packages/auth` | Shared auth middleware |
| `@platform/ui` | `packages/ui` | Shared component library |

Run a command in one workspace with `pnpm --filter @platform/api <cmd>`.

## Running Tests

    pnpm test              # all workspaces
    pnpm --filter @platform/api test

## Contributing

Changes to `packages/*` should include a changeset (`pnpm changeset`) so
dependent apps pick up a version bump.

## License

Proprietary — internal use only.
```
