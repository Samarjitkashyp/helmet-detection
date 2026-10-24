#!/usr/bin/env bash
# Push a new version of the backend code (and model) to an already set-up server.
# Usage:  sudo bash deploy/update.sh      (run from the unzipped new bundle)
# Keeps .env, the database and everything in storage/.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_BACKEND="$(dirname "$HERE")/backend"
APP_DIR=/opt/helmet
[[ -d "$SRC_BACKEND" ]] || { echo "backend/ folder not found next to deploy/." >&2; exit 1; }

PORT="$(cat "$APP_DIR/port" 2>/dev/null || echo 8000)"   # written by the setup script
rsync -a --delete --exclude 'storage/' --exclude '.env' --exclude '__pycache__/' "$SRC_BACKEND/" "$APP_DIR/backend/"
"$APP_DIR/venv/bin/pip" install --no-cache-dir -r "$APP_DIR/backend/requirements.txt"
chown -R helmet:helmet "$APP_DIR"
systemctl restart helmet

for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then echo "Updated. Backend is up."; exit 0; fi
  sleep 3
done
echo "Backend did not come back. Check: journalctl -u helmet -n 80 --no-pager" >&2
exit 1
