#!/usr/bin/env bash
# Nightly PostgreSQL backup, keeps the last 7 days. Installed as /usr/local/bin/helmet-backup by setup_server.sh.
# (Screenshots live in /opt/helmet/backend/storage - cover them with Lightsail snapshots.)
set -euo pipefail
DEST=/var/backups/helmet
mkdir -p "$DEST"
chmod 700 "$DEST"
sudo -u postgres pg_dump helmet_db | gzip > "$DEST/helmet_db_$(date +%F).sql.gz"
find "$DEST" -name 'helmet_db_*.sql.gz' -mtime +7 -delete
