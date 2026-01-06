#!/bin/bash

# Backup script for Telegram Bot Toko

BACKUP_DIR="backups/manual"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $BACKUP_FILE"

# Backup configuration and data
tar -czf "$BACKUP_FILE" \
    config/.env \
    data/exports/ \
    logs/ \
    --exclude='*.log' \
    --exclude='*.tmp'

echo "✅ Backup completed: $BACKUP_FILE"
