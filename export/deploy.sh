#!/usr/bin/env bash
# Разворачивает приглашение на VPS (Ubuntu/Debian) под доменом sonya-anton.ru.
# Запуск без аргументов берёт сайт из git (клонирует или обновляет репозиторий):
#   curl -fsSL https://raw.githubusercontent.com/RykivSale/merrrr/claude/nice-hawking-d7bq5h/tools/deploy.sh | bash
# Или из архива: bash deploy.sh /root/sonya-anton-site.zip
# Повторный запуск обновляет сайт.
set -euo pipefail

DOMAIN="sonya-anton.ru"
REPO_URL="https://github.com/RykivSale/merrrr.git"
BRANCH="claude/nice-hawking-d7bq5h"
REPO="/opt/sonya-anton/repo"
ZIP="${1:-}"
ROOT="/var/www/$DOMAIN"

[ -z "$ZIP" ] || [ -f "$ZIP" ] || { echo "Не найден архив $ZIP"; exit 1; }

export DEBIAN_FRONTEND=noninteractive
# apt на слабом VPS очень медленный — ставим пакеты только если чего-то не хватает
if ! command -v nginx >/dev/null || ! command -v git >/dev/null || ! command -v unzip >/dev/null \
   || ! command -v certbot >/dev/null || ! command -v python3 >/dev/null; then
    echo "==> Ставлю nginx, git, unzip и certbot"
    apt-get update -qq
    apt-get install -y -qq nginx git unzip curl certbot python3-certbot-nginx python3 >/dev/null
fi

echo "==> Раскладываю сайт в $ROOT"
TMP="$(mktemp -d)"
if [ -n "$ZIP" ]; then
    unzip -q "$ZIP" -d "$TMP"
    SRC="$(dirname "$(find "$TMP" -name index.html | head -n1)")"
else
    if [ -d "$REPO/.git" ]; then
        git -C "$REPO" fetch -q origin "$BRANCH"
        git -C "$REPO" reset -q --hard "origin/$BRANCH"
    else
        mkdir -p "$(dirname "$REPO")"
        git clone -q --depth 1 -b "$BRANCH" "$REPO_URL" "$REPO"
    fi
    echo "    коммит $(git -C "$REPO" log -1 --format='%h %s')"
    SRC="$REPO/site"
    cp "$REPO/tools/rsvp_server.py" "$TMP"/
fi
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
# Если certbot уже прописал HTTPS, конфиг не трогаем — иначе повторный деплой его сотрёт
if grep -qs "managed by Certbot" "/etc/nginx/sites-available/$DOMAIN"; then
    echo "    HTTPS-конфиг certbot уже есть, оставляю как есть"
else
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
fi
ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
rm -f /etc/nginx/sites-enabled/default
nginx -t
# nginx сам поднимается после падения и перезагрузки сервера
mkdir -p /etc/systemd/system/nginx.service.d
printf '[Service]\nRestart=always\nRestartSec=3\n' > /etc/systemd/system/nginx.service.d/restart.conf
systemctl daemon-reload
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
