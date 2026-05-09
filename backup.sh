#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env
set -a
source "$SCRIPT_DIR/.env"
set +a

DATA_DIR="$SCRIPT_DIR/data"
BACKUP_DIR="$DATA_DIR/backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# Create tarball of CSV files (skip missing files silently)
tar -czf "$BACKUP_FILE" -C "$DATA_DIR" \
    $(ls "$DATA_DIR"/*.csv 2>/dev/null | xargs -I{} basename {}) 2>/dev/null

if [ ! -s "$BACKUP_FILE" ]; then
    echo "[$TIMESTAMP] No CSV files found, skipping backup."
    exit 0
fi

# Send to Telegram backup group
RESPONSE=$(curl -s -X POST \
    "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" \
    -F "chat_id=$BACKUP_GROUP_ID" \
    -F "document=@$BACKUP_FILE" \
    -F "caption=Backup $TIMESTAMP")

OK=$(echo "$RESPONSE" | grep -o '"ok":true')
if [ -n "$OK" ]; then
    echo "[$TIMESTAMP] Backup sent: $BACKUP_FILE"
else
    echo "[$TIMESTAMP] Backup failed: $RESPONSE"
    exit 1
fi
