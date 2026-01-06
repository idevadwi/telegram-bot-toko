#!/bin/bash

# Monitoring script for Telegram Bot Toko
# Provides comprehensive system status and health checks

echo "=== System Monitoring Report ==="
echo "Date: $(date)"
echo ""

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
echo "💾 Disk usage: $DISK_USAGE"

# Check if disk usage is above 80%
DISK_PERCENT=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_PERCENT -gt 80 ]; then
    echo "⚠️  WARNING: Disk usage is above 80%!"
fi

# Check memory usage
MEM_USAGE=$(free -m | awk 'NR==2 {printf "%.1f%%", $3*100/$2}')
echo "🧠 Memory usage: $MEM_USAGE"

# Check PostgreSQL container
if docker ps | grep -q pg-i5bu; then
    echo "✅ PostgreSQL container is running"
else
    echo "❌ PostgreSQL container is NOT running"
fi

# Check if bot is running
if pgrep -f "python -m src.bot.bot" > /dev/null; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is NOT running"
fi

# Check latest CSV
LATEST_CSV=$(ls -t data/exports/*.csv 2>/dev/null | head -n 1)
if [ -n "$LATEST_CSV" ]; then
    CSV_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_CSV")) / 3600 ))
    echo "📄 Latest CSV age: $CSV_AGE hours"
    
    if [ $CSV_AGE -gt 24 ]; then
        echo "⚠️  WARNING: CSV is older than 24 hours!"
    fi
else
    echo "❌ No CSV files found"
fi

# Check latest backup
LATEST_BACKUP=$(ls -t data/backups/*.i5bu 2>/dev/null | head -n 1)
if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))
    BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
    echo "💾 Latest backup age: $BACKUP_AGE hours (Size: $BACKUP_SIZE)"
else
    echo "❌ No backup files found"
fi

# Check recent sync logs
echo ""
echo "=== Recent Sync Logs (Last 5 Lines) ==="
if [ -f "logs/sync_10am.log" ]; then
    tail -5 logs/sync_10am.log
elif [ -f "logs/sync_7pm.log" ]; then
    tail -5 logs/sync_7pm.log
else
    echo "No sync logs found"
fi

echo ""
echo "=== End Monitoring Report ==="
