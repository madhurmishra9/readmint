# Template: REST API

`backend/templates/rest-api.yaml` — for a public or consumer-facing REST API.

| Section | Required |
|---|---|
| Overview | yes |
| Authentication | yes |
| Endpoints | yes |
| Request/Response Examples | yes |
| Error Handling | no |
| Rate Limiting | no |
| Versioning | no |
| Changelog | no |

## Example README that passes this template

```markdown
# Shortlink API

A REST API for creating and resolving short URLs.

## Overview

The Shortlink API lets clients create short links, look up their targets,
and pull click analytics. Base URL: `https://api.shortlink.example/v1`.

## Authentication

All requests require an API key in the `Authorization` header:

    Authorization: Bearer sk_live_...

Keys are issued from the dashboard and scoped to a single workspace.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/links` | Create a short link |
| `GET` | `/links/:code` | Resolve a short link |
| `GET` | `/links/:code/stats` | Get click counts |
| `DELETE` | `/links/:code` | Deactivate a link |

## Request/Response Examples

Create a link:

    POST /links
    { "url": "https://example.com/blog/post" }

    201 Created
    { "code": "a1B2c3", "short_url": "https://short.link/a1B2c3" }

Resolve a link:

    GET /links/a1B2c3

    200 OK
    { "url": "https://example.com/blog/post", "clicks": 42 }

## Error Handling

Errors return a JSON body with `error.code` and `error.message`. `4xx`
means the request was malformed or unauthorized; `5xx` means retry later.

## Rate Limiting

100 requests/minute per API key. Responses include `X-RateLimit-Remaining`;
exceeding the limit returns `429 Too Many Requests`.

## Versioning

The path prefix (`/v1`) is the version. Breaking changes ship under a new
prefix; `/v1` is supported for at least 12 months after `/v2` ships.

## Changelog

- **2026-05-01** — Added `/links/:code/stats`.
- **2026-01-15** — Initial `v1` release.
```
