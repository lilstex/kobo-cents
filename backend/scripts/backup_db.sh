#!/usr/bin/env bash
# Daily Postgres backup, per docs/backend-architecture/03-phases.md's
# Sub-phase 10.3. Intended to run on the VPS itself (see
# docs/deployment-vps.md for the systemd timer that calls this), not
# from a dev machine. Reads connection details from the same env vars
# the app itself uses, so there is exactly one place DATABASE_URL is
# ever set, not a second copy that can drift out of sync.
#
# Usage: BACKUP_DIR=/var/backups/kobo-and-cents ./backup_db.sh
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/kobo-and-cents}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
DEST="${BACKUP_DIR}/kobo_dev_${TIMESTAMP}.sql.gz"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is not set, refusing to guess a connection" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"

# pg_dump accepts the same postgresql:// URL scheme the app's own
# DATABASE_URL uses, once the +asyncpg driver suffix SQLAlchemy needs
# is stripped back out, pg_dump doesn't know what to do with it.
PG_DUMP_URL="${DATABASE_URL/postgresql+asyncpg:/postgresql:}"

pg_dump "${PG_DUMP_URL}" | gzip > "${DEST}"
echo "Backed up to ${DEST}"

# Retention: delete anything older than RETENTION_DAYS, per Sub-phase
# 10.3, an untested, unbounded pile of backups is its own operational
# risk (disk fills silently), not a real backup strategy.
find "${BACKUP_DIR}" -name 'kobo_dev_*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete
