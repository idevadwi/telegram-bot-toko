#!/bin/bash

# Health check script for Telegram Bot Toko

echo "=== System Health Check ==="
echo "Date: $(date)"
echo ""

# Check if bot is running
if pgrep -f "python -m src.bot.bot" > /dev/null; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is NOT running"
fi

# Check if PostgreSQL is running
if docker ps | grep -q pg-i5bu; then
    echo "✅ PostgreSQL container is running"
else
    echo "❌ PostgreSQL container is NOT running"
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}')
echo "💾 Disk usage: $DISK_USAGE"

# Check latest CSV
LATEST_CSV=$(ls -t data/exports/*.csv 2>/dev/null | head -n 1)
if [ -n "$LATEST_CSV" ]; then
    CSV_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_CSV")) / 3600 ))
    echo "📄 Latest CSV age: $CSV_AGE hours"
else
    echo "❌ No CSV files found"
fi

echo ""
echo "=== End Health Check ==="
