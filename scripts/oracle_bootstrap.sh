#!/usr/bin/env bash
# Run on the Oracle Always Free Ubuntu VM after cloning/uploading the repo.
# Usage: bash scripts/oracle_bootstrap.sh
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Run as the ubuntu/opc user (script will sudo when needed), not as root."
  exit 1
fi

echo "==> Installing Docker Engine + Compose plugin"
sudo apt-get update
sudo apt-get install -y ca-certificates curl git gnupg
sudo install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER" || true

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> Created .env from .env.example — edit POSTGRES_PASSWORD and TRADEPILOT_CORS_ORIGINS before going live"
fi

# Ensure production flags for this host
if ! grep -q '^TRADEPILOT_ENV=production' .env; then
  sed -i 's/^TRADEPILOT_ENV=.*/TRADEPILOT_ENV=production/' .env || echo 'TRADEPILOT_ENV=production' >> .env
fi

echo "==> Building and starting api + worker + postgres"
docker compose -f docker-compose.prod.yaml up -d --build

echo "==> Waiting for Postgres"
for _ in $(seq 1 30); do
  if docker compose -f docker-compose.prod.yaml exec -T postgres pg_isready -U tradepilot -d tradepilot >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> Applying migrations (safe to re-run if already applied — may error on duplicates)"
for f in migrations/0001_init.sql migrations/0002_app_runtime.sql; do
  if [[ -f "$f" ]]; then
    docker compose -f docker-compose.prod.yaml exec -T postgres \
      psql -U tradepilot -d tradepilot -v ON_ERROR_STOP=0 < "$f" || true
  fi
done

echo "==> Health checks"
curl -fsS http://127.0.0.1:8000/health
echo
curl -fsS http://127.0.0.1:8000/ready
echo
echo "Done. Next: put Caddy in front (see docs/oracle-always-free.md) and set Vercel NEXT_PUBLIC_API_URL."
echo "If docker permission denied, log out/in (or run: newgrp docker) and re-run compose."
