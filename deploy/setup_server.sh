#!/usr/bin/env bash
# First-time setup of the Helmet backend on a fresh Ubuntu 22.04/24.04 server (e.g. AWS Lightsail).
# Usage:  sudo bash deploy/setup_server.sh your-domain.com
# Safe to run again: it never overwrites an existing .env, database or uploaded data.
set -euo pipefail

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
  echo "Usage: sudo bash deploy/setup_server.sh your-domain.com" >&2
  exit 1
fi
if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo." >&2
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_BACKEND="$(dirname "$HERE")/backend"
APP_DIR=/opt/helmet
[[ -d "$SRC_BACKEND" ]] || { echo "backend/ folder not found next to deploy/ - unzip the whole bundle." >&2; exit 1; }

echo "==> 1/9 Installing system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y nginx postgresql postgresql-contrib python3-venv python3-pip rsync curl openssl \
  libgl1 libglib2.0-0 certbot python3-certbot-nginx

echo "==> 2/9 Swap file (YOLO + PyTorch can spike in memory)"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> 3/9 Service user and folders"
id helmet &>/dev/null || useradd --system --create-home --home-dir "$APP_DIR" --shell /usr/sbin/nologin helmet
mkdir -p "$APP_DIR/backend"
rsync -a --delete \
  --exclude 'storage/' --exclude '.env' --exclude '__pycache__/' \
  "$SRC_BACKEND/" "$APP_DIR/backend/"
mkdir -p "$APP_DIR/backend/storage/uploads" "$APP_DIR/backend/storage/results"

echo "==> 4/9 Python environment (CPU-only PyTorch; this is the slow step)"
if [[ ! -d "$APP_DIR/venv" ]]; then python3 -m venv "$APP_DIR/venv"; fi
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install torch torchvision --index-url https://download.pytorch.org/whl/cpu
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/backend/requirements.txt"

echo "==> 5/9 PostgreSQL database"
ENV_FILE="$APP_DIR/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  DB_PASS="$(openssl rand -hex 16)"
  SECRET="$(openssl rand -hex 32)"
  sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'helmet_user') THEN
    CREATE ROLE helmet_user LOGIN PASSWORD '${DB_PASS}';
  ELSE
    ALTER ROLE helmet_user PASSWORD '${DB_PASS}';
  END IF;
END \$\$;
SQL
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='helmet_db'" | grep -q 1 \
    || sudo -u postgres createdb -O helmet_user helmet_db
  cat > "$ENV_FILE" <<ENV
APP_ENV=production
DATABASE_URL=postgresql+psycopg2://helmet_user:${DB_PASS}@localhost:5432/helmet_db
SECRET_KEY=${SECRET}
ACCESS_TOKEN_MINUTES=1440

# Optional hardening - uncomment and edit:
# ADMIN_ALLOWED_IPS=203.0.113.10          # only these IPs can open /panel and /admin (comma separated)
# KEEP_ORIGINAL_VIDEOS=false              # delete each uploaded video after it is analysed (saves disk)
ENV
  echo "    created $ENV_FILE with generated secrets (not shown)"
else
  echo "    $ENV_FILE already exists - left untouched"
fi
chmod 600 "$ENV_FILE"
chown -R helmet:helmet "$APP_DIR"

echo "==> 6/9 systemd service"
install -m 644 "$HERE/helmet.service" /etc/systemd/system/helmet.service
systemctl daemon-reload
systemctl enable helmet >/dev/null
systemctl restart helmet

echo "==> 7/9 Waiting for the backend to answer"
for i in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then echo "    backend is up"; break; fi
  sleep 3
  if [[ $i -eq 40 ]]; then echo "Backend did not start. Check: journalctl -u helmet -n 80 --no-pager" >&2; exit 1; fi
done

echo "==> 8/9 nginx"
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "$HERE/nginx-helmet.conf" > /etc/nginx/sites-available/helmet
ln -sf /etc/nginx/sites-available/helmet /etc/nginx/sites-enabled/helmet
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> 9/9 Nightly database backup"
install -m 755 "$HERE/backup.sh" /usr/local/bin/helmet-backup
echo '0 3 * * * root /usr/local/bin/helmet-backup' > /etc/cron.d/helmet-backup

cat <<DONE

Setup finished. Next steps (see deploy/README_DEPLOY.md):
  1. Point the DNS A record of ${DOMAIN} to this server's static IP (if not done yet).
  2. Get the HTTPS certificate (you accept Let's Encrypt's terms):
       sudo certbot --nginx -d ${DOMAIN} --redirect
  3. Create the admin login:
       sudo -u helmet bash -c 'cd ${APP_DIR}/backend && ${APP_DIR}/venv/bin/python -I scripts/create_admin.py'
  4. Test:  https://${DOMAIN}/health
DONE
