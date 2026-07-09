# Template: Contributing Guide

`backend/templates/contributing.yaml` (`doc_type: contributing`) — the same
governance machinery as the README templates, applied to `CONTRIBUTING.md`.

| Section | Required |
|---|---|
| Getting Started | yes |
| Development Setup | yes |
| Branch & Commit Conventions | no |
| Running Tests | yes |
| Submitting a Pull Request | yes |
| Code Style | no |
| Reporting Bugs | no |
| Code of Conduct | no |

## Example CONTRIBUTING.md that passes this template

```markdown
# Contributing to Boardline

Thanks for taking the time to contribute!

## Getting Started

Fork the repo, clone your fork, and add the upstream remote:

    git clone https://github.com/<you>/boardline.git
    cd boardline
    git remote add upstream https://github.com/example/boardline.git

## Development Setup

    npm install
    cp .env.example .env
    npm run dev

## Branch & Commit Conventions

Branch from `main` as `feature/<short-description>` or `fix/<short-description>`.
Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, ...).

## Running Tests

    npm test
    npm run lint

Both must pass before a PR is reviewed.

## Submitting a Pull Request

1. Open an issue first for anything larger than a small fix.
2. Keep PRs focused — one concern per PR.
3. Fill in the PR template, including a test plan.

## Code Style

Formatting is enforced by `npm run lint -- --fix`; don't hand-format.

## Reporting Bugs

Open an issue with reproduction steps, expected vs. actual behavior, and
your environment (OS, Node version).

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
```
