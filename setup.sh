#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root (use sudo)." >&2
    exit 1
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

sed -i "s/FLASK_SECRET_KEY=.*/FLASK_SECRET_KEY=\"$(openssl rand -hex 32)\"/" .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=\"$(openssl rand -hex 16)\"/" .env

echo ".env created with generated secrets."

read -p "Enter download path in host (or press Enter to use default from .env): " HOST_DATA_PATH
if [ ! -z "$HOST_DATA_PATH" ]; then
    if grep -q '^HOST_DATA_PATH=' .env; then
        sed -i "s|^HOST_DATA_PATH=.*$|HOST_DATA_PATH=\"$HOST_DATA_PATH\"|" .env
    else
        echo "HOST_DATA_PATH=\"$HOST_DATA_PATH\"" >> .env
    fi
    echo "HOST_DATA_PATH set to $HOST_DATA_PATH in .env."
else
    echo "Using default HOST_DATA_PATH from .env."
fi

DEFAULT_UID="${SUDO_UID:-$(id -u)}"
read -p "Enter UID for file ownership (or press Enter to use $DEFAULT_UID): " INPUT_UID
INPUT_UID="${INPUT_UID:-$DEFAULT_UID}"
if grep -q '^WIS2DOWNLOADER_UID=' .env; then
    sed -i "s|^WIS2DOWNLOADER_UID=.*$|WIS2DOWNLOADER_UID=\"$INPUT_UID\"|" .env
else
    echo "WIS2DOWNLOADER_UID=\"$INPUT_UID\"" >> .env
fi
echo "WIS2DOWNLOADER_UID set to $INPUT_UID in .env."

if getent group wis2 > /dev/null 2>&1; then
    WIS2_DEFAULT_GID=$(getent group wis2 | cut -d: -f3)
    echo "Group 'wis2' already exists (GID: $WIS2_DEFAULT_GID)."
else
    WIS2_DEFAULT_GID=""
fi

if [ -n "$WIS2_DEFAULT_GID" ]; then
    read -p "Enter GID for file ownership (or press Enter to use wis2 group GID: $WIS2_DEFAULT_GID): " INPUT_GID
else
    read -p "Enter GID for file ownership (or press Enter to create a new 'wis2' group): " INPUT_GID
fi

if [ -z "$INPUT_GID" ]; then
    if [ -z "$WIS2_DEFAULT_GID" ]; then
        groupadd wis2
        INPUT_GID=$(getent group wis2 | cut -d: -f3)
        echo "Created group 'wis2' (GID: $INPUT_GID)."
    else
        INPUT_GID="$WIS2_DEFAULT_GID"
    fi
fi

if grep -q '^WIS2DOWNLOADER_GID=' .env; then
    sed -i "s|^WIS2DOWNLOADER_GID=.*$|WIS2DOWNLOADER_GID=\"$INPUT_GID\"|" .env
else
    echo "WIS2DOWNLOADER_GID=\"$INPUT_GID\"" >> .env
fi
echo "WIS2DOWNLOADER_GID set to $INPUT_GID in .env."

SELECTED_USER=$(getent passwd "$INPUT_UID" | cut -d: -f1 || true)
WIS2_GROUP=$(getent group "$INPUT_GID" | cut -d: -f1 || true)
if [ -n "$SELECTED_USER" ] && [ -n "$WIS2_GROUP" ] && ! id -nG "$SELECTED_USER" | grep -qw "$WIS2_GROUP"; then
    usermod -aG "$WIS2_GROUP" "$SELECTED_USER"
    echo "Added user '$SELECTED_USER' to group '$WIS2_GROUP'. Log out and back in for this to take effect."
fi

EFFECTIVE_DATA_PATH="${HOST_DATA_PATH:-$(grep '^HOST_DATA_PATH=' .env | cut -d= -f2- | tr -d '"')}"
if [ -n "$EFFECTIVE_DATA_PATH" ]; then
    mkdir -p "$EFFECTIVE_DATA_PATH"
    chown -R "$INPUT_UID:$INPUT_GID" "$EFFECTIVE_DATA_PATH"
    echo "Download path '$EFFECTIVE_DATA_PATH' created and owned by $INPUT_UID:$INPUT_GID."
fi

chown "$INPUT_UID:$INPUT_GID" .env

echo "Review .env and adjust any settings before running: docker compose up -d"
