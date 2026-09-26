# VPS Deployment

Hosting decision itself is resolved (a VPS, per `docs/backend-architecture/00.md` and `03-phases.md`'s Phase 12.3), tracked as still-open in `docs/open-items.md`: the actual provider, OS, and setup steps for the real box, and the region confirmation against `00.md`'s Europe-preferred latency reasoning. This file grows once those exist. What follows is what's already real: the backup and restore procedure, Sub-phase 10.3.

## Database backups

`backend/scripts/backup_db.sh` runs `pg_dump` against the same `DATABASE_URL` the app itself uses (stripping the `+asyncpg` driver suffix `pg_dump` doesn't understand), gzips the result, and prunes anything older than `RETENTION_DAYS` (14 by default). `backend/scripts/restore_db.sh` reverses it.

Verified locally: a real backup of the dev database, restored into a fresh database on the same Postgres instance, with a distinguishing test row confirmed present afterward. Not yet verified: an actual restore on the real VPS once one exists, per Sub-phase 10.3's own instruction that "an untested backup doesn't count." The scripts and the daily timer below are the mechanism; running an actual restore drill against production data is a task for once the VPS is real, not something to check off from a local test alone.

### Running it manually

```bash
BACKUP_DIR=/var/backups/kobo-and-cents \
DATABASE_URL=postgresql+asyncpg://kobo:kobo@localhost:5432/kobo_prod \
./backend/scripts/backup_db.sh

DATABASE_URL=postgresql+asyncpg://kobo:kobo@localhost:5432/kobo_prod \
./backend/scripts/restore_db.sh /var/backups/kobo-and-cents/kobo_dev_2026-01-01T00-00-00Z.sql.gz
```

### Daily automation: a systemd timer

Two unit files on the VPS itself, not cron, for real logging and status via `systemctl status`/`journalctl`:

`/etc/systemd/system/kobo-backup.service`:

```ini
[Unit]
Description=Kobo & Cents daily Postgres backup

[Service]
Type=oneshot
EnvironmentFile=/etc/kobo-and-cents/backup.env
WorkingDirectory=/opt/kobo-and-cents/backend
ExecStart=/opt/kobo-and-cents/backend/scripts/backup_db.sh
```

`/etc/systemd/system/kobo-backup.timer`:

```ini
[Unit]
Description=Run kobo-backup.service daily

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

`/etc/kobo-and-cents/backup.env` holds `DATABASE_URL` and `BACKUP_DIR`, readable only by the service account, never committed. Enable with:

```bash
systemctl daemon-reload
systemctl enable --now kobo-backup.timer
```

`Persistent=true` means a backup still runs on the next boot if the VPS happened to be down at 03:00, rather than silently skipping a whole day.

### Restore destination, off-box

Backups living only on the same disk as the database they're backing up survive a bad migration but not a lost VPS. Once the VPS is real, `BACKUP_DIR` should be a mounted off-box volume or the backup step should end with an upload (`rclone`/`aws s3 cp`/similar) to object storage, not local disk alone. Flagged here rather than decided now, since it depends on which storage the actual hosting choice makes cheapest.

## Account deletion

`DELETE /api/v1/account` (Sub-phase 10.4) sets `deleted_at` and anonymizes the `users` row's personal fields (email replaced with a non-reusable placeholder, password hash invalidated), leaving `subscriptions` and `payment_events` untouched, per `docs/backend-architecture/02.md`. The exact retention period before an anonymized row is ever purged for good is a real NDPR question that doc explicitly flags as unresolved and not something to guess at; this endpoint implements the deletion request mechanism itself, which is correct regardless of what that period turns out to be, not the retention policy.
