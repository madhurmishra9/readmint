# Template: Docker Image

`backend/templates/docker-image.yaml` — for a published Docker/OCI image.

| Section | Required |
|---|---|
| Overview | yes |
| Supported Tags | yes |
| Quick Start | yes |
| Environment Variables | yes |
| Volumes | no |
| Ports | no |
| Building the Image | no |
| License | no |

## Example README that passes this template

```markdown
# example/mailhog-lite

A lightweight SMTP test server for local development, packaged as a
container image.

## Overview

`mailhog-lite` catches outbound SMTP mail from your app during local
development and shows it in a web UI, so you don't send real email while
testing signup flows.

## Supported Tags

| Tag | Base | Notes |
|---|---|---|
| `latest`, `1.4` | `alpine:3.20` | Recommended |
| `1.4-debug` | `debian:bookworm-slim` | Includes a shell for debugging |

## Quick Start

    docker run -p 1025:1025 -p 8025:8025 example/mailhog-lite:1.4

Point your app's SMTP client at `localhost:1025`, then view captured mail
at `http://localhost:8025`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SMTP_PORT` | `1025` | Port the SMTP server listens on |
| `UI_PORT` | `8025` | Port the web UI listens on |
| `RETENTION_HOURS` | `24` | How long captured messages are kept |

## Volumes

Mount `/data` to persist captured messages across container restarts:

    docker run -v mailhog-data:/data example/mailhog-lite:1.4

## Ports

- `1025/tcp` — SMTP
- `8025/tcp` — Web UI

## Building the Image

    docker build -t example/mailhog-lite:local .

## License

MIT
```
