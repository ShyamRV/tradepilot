#!/usr/bin/env bash
# Postgres dump / restore drill for TradePilot.
# Usage:
#   ./scripts/backup_restore.sh backup  [outfile]
#   ./scripts/backup_restore.sh restore <dumpfile>
#   ./scripts/backup_restore.sh drill
#
# Requires DATABASE_URL (postgresql://...) or PG* env vars.
# Prefer an isolated restore target; never restore production dumps onto live
# writers without an approved incident/cutover.

set -euo pipefail

MODE="${1:-}"
ARG="${2:-}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

require_tools() {
  command -v pg_dump >/dev/null
  command -v pg_restore >/dev/null || command -v psql >/dev/null
}

resolve_url() {
  if [[ -n "${DATABASE_URL:-}" ]]; then
    echo "$DATABASE_URL"
    return
  fi
  echo "DATABASE_URL is required" >&2
  exit 1
}

backup() {
  require_tools
  local url outfile
  url="$(resolve_url)"
  outfile="${ARG:-$BACKUP_DIR/tradepilot_$STAMP.dump}"
  echo "Backing up to $outfile"
  pg_dump --format=custom --no-owner --no-acl --dbname="$url" --file="$outfile"
  echo "Backup complete: $outfile"
  echo "Record backup_timestamp=$STAMP for the restore drill."
}

restore() {
  require_tools
  local url dump
  url="$(resolve_url)"
  dump="${ARG:-}"
  if [[ -z "$dump" || ! -f "$dump" ]]; then
    echo "Usage: $0 restore <dumpfile>" >&2
    exit 1
  fi
  if [[ "${ALLOW_DESTRUCTIVE_RESTORE:-}" != "yes" ]]; then
    echo "Refusing restore. Set ALLOW_DESTRUCTIVE_RESTORE=yes after confirming the target is isolated." >&2
    exit 1
  fi
  echo "Restoring $dump into DATABASE_URL target"
  if command -v pg_restore >/dev/null; then
    pg_restore --clean --if-exists --no-owner --no-acl --dbname="$url" "$dump"
  else
    psql --dbname="$url" -v ON_ERROR_STOP=1 -f "$dump"
  fi
  echo "Restore finished. Run migration/version, RLS, and smoke checks from docs/runbooks.md."
}

drill() {
  local dump
  dump="$BACKUP_DIR/tradepilot_drill_$STAMP.dump"
  echo "=== Backup/restore drill start ($STAMP) ==="
  ARG="$dump" backup
  echo "Drill backup written. To complete the drill:"
  echo "  1. Point DATABASE_URL at an isolated empty database."
  echo "  2. ALLOW_DESTRUCTIVE_RESTORE=yes $0 restore $dump"
  echo "  3. Verify checksums, migration version, RLS, sampled tenant isolation."
  echo "  4. Record RPO/RTO evidence in the incident/acceptance log."
  echo "=== Drill backup phase complete ==="
}

case "$MODE" in
  backup) backup ;;
  restore) restore ;;
  drill) drill ;;
  *)
    echo "Usage: $0 {backup|restore|drill} [path]" >&2
    exit 1
    ;;
esac
