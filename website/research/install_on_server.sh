#!/usr/bin/env bash
# Installs the Axom AI research pages next to the existing aiaxom.co.in apps. Safe to run again.
# Usage on the server:  sudo bash install_on_server.sh research_site.tar axom-research.nginx.conf
# Changes: /var/www/axom-research (new), /etc/nginx/snippets/axom-research.conf (new) and ONE include line in
# /etc/nginx/conf.d/aiaxom.co.in.conf (backed up first; restored automatically if nginx -t fails).
set -euo pipefail
TAR="$1"; SNIPPET="$2"
CONF=/etc/nginx/conf.d/aiaxom.co.in.conf
LINE='    include /etc/nginx/snippets/axom-research.conf;'
ANCHOR='# Next.js Static chunks & assets'
OWNER="${SUDO_USER:-admin}"

[[ $EUID -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
install -d -o "$OWNER" -g "$OWNER" /var/www/axom-research
rm -rf /var/www/axom-research/research /var/www/axom-research/llms.txt
tar -xf "$TAR" -C /var/www/axom-research
chown -R "$OWNER":"$OWNER" /var/www/axom-research
find /var/www/axom-research -type d -exec chmod 755 {} +
find /var/www/axom-research -type f -exec chmod 644 {} +

cp "$SNIPPET" /etc/nginx/snippets/axom-research.conf
if ! grep -qF "snippets/axom-research.conf" "$CONF"; then
  BACKUP="$CONF.bak-$(date +%Y%m%d_%H%M%S)"
  cp "$CONF" "$BACKUP"
  python3 - "$CONF" "$ANCHOR" "$LINE" <<'PY'
import sys
conf, anchor, line = sys.argv[1:4]
lines = open(conf).read().split("\n")
for i, l in enumerate(lines):
    if anchor in l:
        lines[i:i] = ["    # Axom AI Research (static pages)", line, ""]
        break
else:
    sys.exit("anchor not found in " + conf)
open(conf, "w").write("\n".join(lines))
PY
  if ! nginx -t 2>/tmp/nginx-test.log; then
    echo "nginx -t failed, restoring the old config:"; cat /tmp/nginx-test.log
    cp "$BACKUP" "$CONF"; nginx -t; exit 1
  fi
else
  nginx -t
fi
systemctl reload nginx
echo "Research pages installed."
