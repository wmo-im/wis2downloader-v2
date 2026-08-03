#!/usr/bin/env bash
set -euo pipefail

# GNU sed (Linux, Git Bash on Windows) takes `-i suffix`, BSD sed (macOS)
# requires the suffix as a separate argument even when empty.
if sed --version >/dev/null 2>&1; then
    sedi() { sed -i "$@"; }
else
    sedi() { sed -i '' "$@"; }
fi

ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')
if docker plugin ls | grep -q 'loki'; then
    echo "Loki Docker plugin already installed."
else
    docker plugin install grafana/loki-docker-driver:3.6.7-${ARCH} --alias loki --grant-all-permissions
    echo "Loki Docker plugin installed."
fi

if [ -f .env ]; then
    echo ".env already exists — remove it first if you want to regenerate secrets."
    exit 1
fi

cp default.env .env

sedi "s/FLASK_SECRET_KEY=.*/FLASK_SECRET_KEY=\"$(openssl rand -hex 32)\"/" .env
sedi "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=\"$(openssl rand -hex 16)\"/" .env

echo ".env created with generated secrets."

read -p "Enter download path in host (or press Enter to use default from .env): " HOST_DATA_PATH
if [ ! -z "$HOST_DATA_PATH" ]; then
    if grep -q '^HOST_DATA_PATH=' .env; then
        sedi "s|^HOST_DATA_PATH=.*$|HOST_DATA_PATH=\"$HOST_DATA_PATH\"|" .env
    else
        echo "HOST_DATA_PATH=\"$HOST_DATA_PATH\"" >> .env
    fi
    echo "HOST_DATA_PATH set to $HOST_DATA_PATH in .env."
else
    echo "Using default HOST_DATA_PATH from .env."
fi

read -p "Enter Grafana admin username (or press Enter to use default 'admin'): " GRAFANA_ADMIN_USER
GRAFANA_ADMIN_USER="${GRAFANA_ADMIN_USER:-admin}"
sedi "s|^GRAFANA_ADMIN_USER=.*$|GRAFANA_ADMIN_USER=\"$GRAFANA_ADMIN_USER\"|" .env
echo "GRAFANA_ADMIN_USER set to '$GRAFANA_ADMIN_USER' in .env."

read -p "Enter Grafana admin password (or press Enter to auto-generate): " GRAFANA_ADMIN_PASSWORD
if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    GRAFANA_ADMIN_PASSWORD="$(openssl rand -hex 16)"
    echo "Auto-generated Grafana password: $GRAFANA_ADMIN_PASSWORD"
fi
sedi "s|^GRAFANA_ADMIN_PASSWORD=.*$|GRAFANA_ADMIN_PASSWORD=\"$GRAFANA_ADMIN_PASSWORD\"|" .env
echo "GRAFANA_ADMIN_PASSWORD set in .env."

read -p "Enter UID for file ownership (or press Enter to use current user's UID: $(id -u)): " INPUT_UID
INPUT_UID="${INPUT_UID:-$(id -u)}"
if grep -q '^WIS2DOWNLOADER_UID=' .env; then
    sedi "s|^WIS2DOWNLOADER_UID=.*$|WIS2DOWNLOADER_UID=\"$INPUT_UID\"|" .env
else
    echo "WIS2DOWNLOADER_UID=\"$INPUT_UID\"" >> .env
fi
echo "WIS2DOWNLOADER_UID set to $INPUT_UID in .env."

read -p "Enter GID for file ownership (or press Enter to use current user's GID: $(id -g)): " INPUT_GID
INPUT_GID="${INPUT_GID:-$(id -g)}"
if grep -q '^WIS2DOWNLOADER_GID=' .env; then
    sedi "s|^WIS2DOWNLOADER_GID=.*$|WIS2DOWNLOADER_GID=\"$INPUT_GID\"|" .env
else
    echo "WIS2DOWNLOADER_GID=\"$INPUT_GID\"" >> .env
fi
echo "WIS2DOWNLOADER_GID set to $INPUT_GID in .env."

EFFECTIVE_DATA_PATH="${HOST_DATA_PATH:-$(grep '^HOST_DATA_PATH=' .env | cut -d= -f2- | tr -d '"')}"
if [ -n "$EFFECTIVE_DATA_PATH" ]; then
    mkdir -p "$EFFECTIVE_DATA_PATH"
    echo "Download path '$EFFECTIVE_DATA_PATH' created."
fi

echo "Review .env and adjust any settings before running: docker compose up -d"
