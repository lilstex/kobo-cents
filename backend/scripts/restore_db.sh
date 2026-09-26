#!/usr/bin/env bash
# Restores a backup produced by backup_db.sh. Per docs/backend-
# architecture/03-phases.md's Sub-phase 10.3: "an untested backup
# doesn't count," this script exists specifically so that claim is
# checkable, not just a backup existing.
#
# Usage: DATABASE_URL=postgresql+asyncpg://... ./restore_db.sh path/to/backup.sql.gz
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 path/to/backup.sql.gz" >&2
  exit 1
fi
BACKUP_FILE="$1"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set, refusing to guess a connection" >&2
  exit 1
fi

PG_DUMP_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"

gunzip -c "${BACKUP_FILE}" | psql "${PG_DUMP_URL}"
echo "Restored ${BACKUP_FILE}"
