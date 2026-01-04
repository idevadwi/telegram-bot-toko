#!/bin/bash

# Backup configuration files for Telegram Bot Toko
# Creates timestamped backups of critical configuration files

BACKUP_DIR="backups/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating configuration backup: $BACKUP_FILE"

tar -czf "$BACKUP_FILE" \
    config/.env \
    docker/docker-compose.yml \
    scripts/ \
    --exclude='*.pyc' \
    --exclude='__pycache__'

if [ $? -eq 0 ]; then
    echo "✅ Configuration backup completed: $BACKUP_FILE"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "📦 Backup size: $BACKUP_SIZE"
else
    echo "❌ Configuration backup failed"
    exit 1
fi
