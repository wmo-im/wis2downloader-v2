#!/usr/bin/env bash
set -euo pipefail

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

read -p "Enter UID for file ownership (or press Enter to use current user's UID: $(id -u)): " INPUT_UID
INPUT_UID="${INPUT_UID:-$(id -u)}"
if grep -q '^WIS2DOWNLOADER_UID=' .env; then
    sed -i "s|^WIS2DOWNLOADER_UID=.*$|WIS2DOWNLOADER_UID=\"$INPUT_UID\"|" .env
else
    echo "WIS2DOWNLOADER_UID=\"$INPUT_UID\"" >> .env
fi
echo "WIS2DOWNLOADER_UID set to $INPUT_UID in .env."

read -p "Enter GID for file ownership (or press Enter to use current user's GID: $(id -g)): " INPUT_GID
INPUT_GID="${INPUT_GID:-$(id -g)}"
if grep -q '^WIS2DOWNLOADER_GID=' .env; then
    sed -i "s|^WIS2DOWNLOADER_GID=.*$|WIS2DOWNLOADER_GID=\"$INPUT_GID\"|" .env
else
    echo "WIS2DOWNLOADER_GID=\"$INPUT_GID\"" >> .env
fi
echo "WIS2DOWNLOADER_GID set to $INPUT_GID in .env."

echo "Review .env and adjust any settings before running: docker compose up -d"
