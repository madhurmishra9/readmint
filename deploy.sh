#!/usr/bin/env bash
#
# Readmint one-click deploy (macOS / Linux).
#
#   ./deploy.sh            # build + run on http://localhost:8080 (stub LLM)
#   PORT=9000 ./deploy.sh  # use a different host port
#
# A root .env file (if present) is passed into the container, so you can drop
# RF_LLM_* there to point at a live Cortex endpoint instead of the stub.
set -euo pipefail

IMAGE="readmint:local"
NAME="readmint"
PORT="${PORT:-8080}"
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "✗ Docker is not installed. Get it at https://docs.docker.com/get-docker/" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "✗ Docker is installed but the daemon isn't running. Start Docker Desktop and retry." >&2
  exit 1
fi

echo "→ Building $IMAGE …"
docker build -t "$IMAGE" .

echo "→ Replacing any existing container …"
docker rm -f "$NAME" >/dev/null 2>&1 || true

# Make a host-side local LLM (e.g. Ollama on :11434) reachable from the container.
ENV_ARGS=(--add-host=host.docker.internal:host-gateway)
if [ -f .env ]; then
  ENV_ARGS+=(--env-file .env)
  echo "→ Using .env for configuration"
else
  ENV_ARGS+=(-e "RF_LOCAL_LLM_BASE_URL=http://host.docker.internal:11434/v1")
  echo "→ No .env — will auto-detect a local LLM on the host (Ollama :11434), else stub"
fi

echo "→ Starting container on port $PORT …"
docker run -d --name "$NAME" -p "${PORT}:8080" "${ENV_ARGS[@]}" "$IMAGE" >/dev/null

URL="http://localhost:${PORT}"
echo -n "→ Waiting for health"
for _ in $(seq 1 30); do
  if curl -fsS "${URL}/healthz" >/dev/null 2>&1; then
    echo " — ready."
    echo "✓ Readmint is live at ${URL} (API docs at ${URL}/docs)"
    command -v open    >/dev/null 2>&1 && open "$URL" && exit 0
    command -v xdg-open >/dev/null 2>&1 && xdg-open "$URL" && exit 0
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo "" >&2
echo "✗ Container started but never became healthy. Logs:" >&2
docker logs "$NAME" >&2
exit 1
