#!/usr/bin/env bash
# Разворачивает приглашение на VPS (Ubuntu/Debian) под доменом sonya-anton.ru.
# Запуск: bash deploy.sh [путь к архиву]   (по умолчанию /root/sonya-anton-site.zip)
# Повторный запуск с новым архивом обновляет сайт.
set -euo pipefail

DOMAIN="sonya-anton.ru"
ZIP="${1:-/root/sonya-anton-site.zip}"
ROOT="/var/www/$DOMAIN"

[ -f "$ZIP" ] || { echo "Не найден архив $ZIP — загрузите sonya-anton-site.zip в /root"; exit 1; }

echo "==> Ставлю nginx, unzip и certbot"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx unzip certbot python3-certbot-nginx >/dev/null

echo "==> Раскладываю сайт в $ROOT"
TMP="$(mktemp -d)"
unzip -q "$ZIP" -d "$TMP"
SRC="$(dirname "$(find "$TMP" -name index.html | head -n1)")"
mkdir -p "$ROOT"
rm -rf "${ROOT:?}"/*
cp -r "$SRC"/. "$ROOT"/
chown -R www-data:www-data "$ROOT"
SRV="$(find "$TMP" -name rsvp_server.py | head -n1)"
mkdir -p /opt/sonya-anton /var/lib/sonya-anton
cp "$SRV" /opt/sonya-anton/rsvp_server.py
chown -R www-data:www-data /var/lib/sonya-anton
rm -rf "$TMP"

echo "==> Настраиваю сервис опроса (ответы в /var/lib/sonya-anton/rsvp.json)"
apt-get install -y -qq python3 >/dev/null
cat > /etc/systemd/system/sonya-rsvp.service <<EOF
[Unit]
Description=Sonya and Anton RSVP
After=network.target

[Service]
User=www-data
ExecStart=/usr/bin/python3 /opt/sonya-anton/rsvp_server.py 8787 /var/lib/sonya-anton/rsvp.json
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable sonya-rsvp >/dev/null
systemctl restart sonya-rsvp

echo "==> Настраиваю nginx"
cat > "/etc/nginx/sites-available/$DOMAIN" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    root $ROOT;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8787;
        proxy_set_header X-Real-IP \$remote_addr;
        client_max_body_size 4k;
    }
    location / {
        try_files \$uri \$uri/ =404;
    }
    location ~* \.(jpg|png|svg|mp3|woff2)\$ {
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF
ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx >/dev/null
systemctl reload nginx

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    ufw allow "Nginx Full" >/dev/null
fi

echo "==> Проверяю, что домен смотрит на этот сервер"
MY_IP="$(curl -4 -s --max-time 5 https://ifconfig.me || hostname -I | awk '{print $1}')"
DNS_IP="$(getent ahostsv4 "$DOMAIN" | awk 'NR==1{print $1}' || true)"
if [ "$DNS_IP" = "$MY_IP" ]; then
    echo "==> Выпускаю HTTPS-сертификат"
    certbot --nginx -n --agree-tos --register-unsafely-without-email --redirect \
        -d "$DOMAIN" $(getent ahostsv4 "www.$DOMAIN" >/dev/null && echo "-d www.$DOMAIN")
    echo "Готово: https://$DOMAIN"
else
    echo "Сайт работает по http://$MY_IP"
    echo "Домен $DOMAIN пока указывает на '${DNS_IP:-ничего}', а сервер — $MY_IP."
    echo "Пропишите в reg.ru A-записи @ и www -> $MY_IP, подождите и запустите скрипт ещё раз для HTTPS."
fi
