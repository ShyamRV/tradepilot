#!/bin/sh
# Free-tier Render entrypoint: API (binds $PORT) + Telegram worker in one service.
# Background workers are paid on Render; packing both keeps the stack at $0.
set -eu

PORT="${PORT:-8000}"

python -m apps.worker.main &
WORKER_PID=$!

cleanup() {
  kill "$WORKER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

exec uvicorn apps.api.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips "*"
