#!/usr/bin/env bash
# Разворачивает приглашение на VPS (Ubuntu/Debian) через Docker Compose: Caddy + HTTPS + сервис опроса.
# Запуск на сервере: curl -fsSL https://raw.githubusercontent.com/RykivSale/merrrr/claude/nice-hawking-d7bq5h/tools/deploy_docker.sh | bash
# Повторный запуск обновляет сайт из git.
set -euo pipefail

REPO_URL="https://github.com/RykivSale/merrrr.git"
BRANCH="claude/nice-hawking-d7bq5h"
REPO="/opt/sonya-anton/repo"
export DEBIAN_FRONTEND=noninteractive

# Освобождаем 80/443 после старой установки на nginx
systemctl disable --now nginx sonya-rsvp 2>/dev/null || true

if ! command -v docker >/dev/null; then
    echo "==> Ставлю Docker"
    apt-get update -qq
    apt-get install -y -qq git curl ca-certificates >/dev/null
    curl -fsSL https://get.docker.com | sh >/dev/null
fi
apt-get install -y -qq git >/dev/null

echo "==> Забираю сайт из git"
if [ -d "$REPO/.git" ]; then
    git -C "$REPO" fetch -q origin "$BRANCH"
    git -C "$REPO" reset -q --hard "origin/$BRANCH"
else
    rm -rf "$REPO"; mkdir -p "$(dirname "$REPO")"
    git clone -q --depth 1 -b "$BRANCH" "$REPO_URL" "$REPO"
fi
echo "    коммит $(git -C "$REPO" log -1 --format='%h %s')"

if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
    ufw allow 80,443/tcp >/dev/null
fi

echo "==> Запускаю контейнеры"
cd "$REPO"
docker compose up -d --build
docker compose ps
echo "Готово: https://sonya-anton.ru (сертификат Caddy выпустит, когда DNS начнёт указывать на этот сервер)"
