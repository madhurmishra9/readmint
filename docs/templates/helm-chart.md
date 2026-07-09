# Template: Helm Chart

`backend/templates/helm-chart.yaml` — for a Kubernetes Helm chart.

| Section | Required |
|---|---|
| Overview | yes |
| Prerequisites | yes |
| Installing the Chart | yes |
| Uninstalling the Chart | no |
| Configuration | yes |
| Values | yes |
| Contributing | no |
| License | no |

## Example README that passes this template

```markdown
# queue-worker

A Helm chart that deploys a horizontally-scalable background job worker.

## Overview

This chart deploys a `Deployment` of worker pods that consume from a
message queue, plus an optional `HorizontalPodAutoscaler` keyed on queue
depth.

## Prerequisites

- Kubernetes 1.28+
- Helm 3.14+
- A reachable queue endpoint (Redis or SQS)

## Installing the Chart

    helm repo add example https://charts.example.com
    helm install my-worker example/queue-worker \
      --set queue.url=redis://redis:6379

## Uninstalling the Chart

    helm uninstall my-worker

## Configuration

Configuration is supplied via `--set` or a `values.yaml` override file:

    helm install my-worker example/queue-worker -f my-values.yaml

## Values

| Key | Default | Description |
|---|---|---|
| `replicaCount` | `2` | Number of worker pods |
| `queue.url` | `""` | Queue connection string (required) |
| `resources.limits.cpu` | `500m` | Per-pod CPU limit |
| `autoscaling.enabled` | `false` | Enable HPA on queue depth |

## Contributing

Bump `Chart.yaml` version on any template change; run `helm lint .` before
opening a PR.

## License

Apache-2.0
```
