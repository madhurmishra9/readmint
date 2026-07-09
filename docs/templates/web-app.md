# Template: Web Application

`backend/templates/web-app.yaml` — for a frontend or full-stack web app.

| Section | Required |
|---|---|
| Overview | yes |
| Features | no |
| Tech Stack | no |
| Getting Started | yes |
| Environment Variables | yes |
| Scripts | no |
| Deployment | yes |
| Contributing | no |
| License | no |

## Example README that passes this template

```markdown
# Boardline

A kanban board for small teams, built with React and a Postgres-backed API.

## Overview

Boardline gives a team a shared board of columns and cards, with drag-and-drop
reordering, per-card comments, and email digests of what moved overnight.

## Features

- Drag-and-drop cards across columns
- Real-time updates via WebSockets
- Per-board access control

## Tech Stack

React, Vite, TanStack Query, Node/Express, Postgres.

## Getting Started

    git clone https://github.com/example/boardline.git
    cd boardline
    npm install
    npm run dev

The app is served at `http://localhost:5173`, proxying API calls to
`http://localhost:4000`.

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `SESSION_SECRET` | Cookie signing secret |
| `VITE_API_URL` | Base URL the frontend calls |

Copy `.env.example` to `.env` and fill these in before running `npm run dev`.

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start frontend + API in watch mode |
| `npm run build` | Production build |
| `npm test` | Run the Vitest suite |

## Deployment

Push to `main` to trigger the `deploy.yml` GitHub Action, which builds the
frontend, runs migrations against `DATABASE_URL`, and deploys to Fly.io.

## Contributing

Open an issue before large changes; run `npm run lint` before submitting a PR.

## License

Apache-2.0
```
