# VPS Deployment Guide - Telegram Bot Toko

This guide provides step-by-step instructions for deploying the Telegram Bot Toko system to a Virtual Private Server (VPS).

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Project Setup](#project-setup)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Testing](#testing)
7. [Automation with Cron Jobs](#automation-with-cron-jobs)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Security Hardening](#security-hardening)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### VPS Requirements

- **Operating System**: Ubuntu 20.04 LTS or 22.04 LTS (recommended)
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: Minimum 20GB
- **CPU**: 2 cores minimum
- **Network**: Stable internet connection

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.8+
- Git
- Cron (usually pre-installed)
- Nginx (optional, for reverse proxy)

### Required Accounts

- **GitHub/GitLab**: For cloning the repository
- **Telegram Bot**: Create via [@BotFather](https://t.me/botfather)
- **Dropbox**: For API credentials (App Key, App Secret, Refresh Token)

---

## Server Preparation

### Step 1: Connect to Your VPS

```bash
ssh root@your-vps-ip-address
```

### Step 2: Update System Packages

```bash
apt update && apt upgrade -y
```

### Step 3: Install Required Packages

```bash
# Install basic utilities
apt install -y curl wget git vim htop net-tools

# Install Python 3 and pip
apt install -y python3 python3-pip python3-venv

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
python3 --version
```

### Step 4: Create a Non-Root User (Recommended)

```bash
# Create user
adduser telegrambot

# Add user to sudo and docker groups
usermod -aG sudo telegrambot
usermod -aG docker telegrambot

# Switch to the new user
su - telegrambot
```

### Step 5: Configure Firewall (Optional)

```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS (if using Nginx)
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
```

---

## Project Setup

### Step 1: Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone <your-repository-url> telegram-bot-toko
cd telegram-bot-toko
```

### Step 2: Create Required Directories

```bash
# Create data directories
mkdir -p data/backups
mkdir -p data/exports
mkdir -p logs
mkdir -p backups/manual

# Set permissions
chmod 755 data/backups
chmod 755 data/exports
chmod 755 logs
chmod 755 backups/manual
```

### Step 3: Install Python Dependencies

```bash
# Install requirements
pip3 install -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Set Script Permissions

```bash
# Make shell scripts executable
chmod +x scripts/backup.sh
chmod +x scripts/health_check.sh
```

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy example environment file
cp config/.env.example config/.env

# Edit the file
vim config/.env
```

### Step 2: Configure Telegram Bot

#### Get Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided

#### Get Admin Chat ID

1. Start a conversation with your bot
2. Send any message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your `chat_id` in the response

Update [`config/.env`](config/.env):

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_CHAT_ID=123456789
```

### Step 3: Configure Dropbox API

#### Create Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create App"
3. Choose "Scoped access" and select your Dropbox account
4. Name your app (e.g., "Telegram Bot Toko")
5. Select "Files and datastores" permission type
6. Select "Yes - My app only needs access to files it creates"
7. Enter the folder path (e.g., `/IPOS`)
8. Create the app

#### Generate Refresh Token

1. In your app settings, go to "Permissions"
2. Add these scopes:
   - `files.metadata.read`
   - `files.content.read`
3. Go to "Settings" and generate an access token
4. Use the [Dropbox OAuth2 Playground](https://dropbox.github.io/dropbox-api-v2-explorer/#oauth2/token) to get a refresh token

Update [`config/.env`](config/.env):

```bash
# Dropbox Configuration
DROPBOX_APP_KEY=your_app_key_here
DROPBOX_APP_SECRET=your_app_secret_here
DROPBOX_REFRESH_TOKEN=your_refresh_token_here
DROPBOX_FOLDER_PATH=/IPOS
```

### Step 4: Configure Database

Update [`config/.env`](config/.env):

```bash
# Database Configuration
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
```

### Step 5: Configure Paths

Update [`config/.env`](config/.env) with your actual paths:

```bash
# Path Configuration
PROJECT_ROOT=/home/telegrambot/telegram-bot-toko
DATA_DIR=/home/telegrambot/telegram-bot-toko/data
BACKUPS_DIR=/home/telegrambot/telegram-bot-toko/data/backups
EXPORTS_DIR=/home/telegrambot/telegram-bot-toko/data/exports
LOGS_DIR=/home/telegrambot/telegram-bot-toko/logs

# Application Configuration
MAX_CSV_FILES=5
LOG_LEVEL=INFO
```

### Step 6: Secure Environment File

```bash
# Set restrictive permissions
chmod 600 config/.env

# Verify it's not readable by others
ls -la config/.env
```

---

## Database Setup

### Step 1: Start PostgreSQL Container

```bash
# Start Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Check if container is running
docker ps | grep pg-i5bu
```

### Step 2: Verify Database Connection

```bash
# Check database logs
docker logs pg-i5bu

# Test connection
docker exec -u postgres pg-i5bu psql -U postgres -c "SELECT version();"
```

### Step 3: Create Initial Backup (Optional)

```bash
# Run manual backup
./scripts/backup.sh
```

---

## Testing

### Step 1: Test Sync Process

```bash
# Run sync process
python scripts/sync.py

# Check output
ls -lh data/backups/
ls -lh data/exports/
```

### Step 2: Test Health Check

```bash
# Run health check
./scripts/health_check.sh
```

Expected output:
```
=== System Health Check ===
Date: [current date]

✅ Bot is NOT running (expected)
✅ PostgreSQL container is running
💾 Disk usage: [percentage]
📄 Latest CSV age: [hours]
=== End Health Check ===
```

### Step 3: Test Telegram Bot

```bash
# Start bot in foreground
python -m src.bot.bot
```

In Telegram:
1. Send `/start` to your bot
2. Try searching for a product
3. Test `/reload` command
4. Test `/version` command

### Step 4: Run Unit Tests

```bash
# Run tests
pytest tests/ -v
```

---

## Automation with Cron Jobs

### Step 1: Edit Crontab

```bash
# Open crontab editor
crontab -e
```

### Step 2: Add Cron Jobs

Add the following entries to your crontab:

```bash
# ========================================
# Telegram Bot Toko - Cron Jobs
# ========================================

# Sync at 10:00 AM daily (morning update)
0 10 * * * cd /home/telegrambot/telegram-bot-toko && /home/telegrambot/telegram-bot-toko/venv/bin/python scripts/sync.py >> logs/sync_10am.log 2>&1

# Sync at 7:00 PM daily (evening update)
0 19 * * * cd /home/telegrambot/telegram-bot-toko && /home/telegrambot/telegram-bot-toko/venv/bin/python scripts/sync.py >> logs/sync_7pm.log 2>&1

# Health check every hour
0 * * * * cd /home/telegrambot/telegram-bot-toko && ./scripts/health_check.sh >> logs/health.log 2>&1

# Manual backup daily at 11:00 PM
0 23 * * * cd /home/telegrambot/telegram-bot-toko && ./scripts/backup.sh >> logs/backup.log 2>&1

# Log rotation - Clean old logs weekly
0 2 * * 0 find /home/telegrambot/telegram-bot-toko/logs -name "*.log" -mtime +30 -delete
```

### Step 3: Verify Cron Jobs

```bash
# List current cron jobs
crontab -l

# Check cron service status
systemctl status cron
```

### Step 4: Test Cron Jobs

```bash
# Test sync manually (simulating cron)
cd /home/telegrambot/telegram-bot-toko
/home/telegrambot/telegram-bot-toko/venv/bin/python scripts/sync.py >> logs/sync_test.log 2>&1

# Check the log
cat logs/sync_test.log
```

---

## Monitoring and Maintenance

### Step 1: Set Up Log Rotation

Create log rotation configuration:

```bash
sudo vim /etc/logrotate.d/telegram-bot-toko
```

Add the following content:

```bash
/home/telegrambot/telegram-bot-toko/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 telegrambot telegrambot
    sharedscripts
    postrotate
        # Optional: restart bot if needed
    endscript
}
```

### Step 2: Monitor Disk Space

```bash
# Check disk usage
df -h

# Check directory sizes
du -sh /home/telegrambot/telegram-bot-toko/*
```

### Step 3: Monitor Logs

```bash
# View recent sync logs
tail -f logs/sync_10am.log

# View health check logs
tail -f logs/health.log

# View backup logs
tail -f logs/backup.log
```

### Step 4: Monitor Docker Containers

```bash
# Check container status
docker ps

# View container logs
docker logs pg-i5bu --tail 100 -f

# Check container resource usage
docker stats pg-i5bu
```

### Step 5: Create Monitoring Script

Create a monitoring script:

```bash
vim scripts/monitor.sh
```

Add the following content:

```bash
#!/bin/bash

# Monitoring script for Telegram Bot Toko

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

# Check recent sync logs
echo ""
echo "=== Recent Sync Logs ==="
tail -5 logs/sync_10am.log 2>/dev/null || echo "No sync logs found"

echo ""
echo "=== End Monitoring Report ==="
```

Make it executable:

```bash
chmod +x scripts/monitor.sh
```

Run it:

```bash
./scripts/monitor.sh
```

---

## Security Hardening

### Step 1: Secure SSH Access

```bash
# Edit SSH configuration
sudo vim /etc/ssh/sshd_config

# Make these changes:
# - Disable root login: PermitRootLogin no
# - Disable password authentication: PasswordAuthentication no
# - Use only key-based authentication

# Restart SSH service
sudo systemctl restart sshd
```

### Step 2: Set Up SSH Key Authentication

On your local machine:

```bash
# Generate SSH key pair (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to VPS
ssh-copy-id telegrambot@your-vps-ip-address
```

### Step 3: Configure Fail2Ban (Optional)

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create local configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo vim /etc/fail2ban/jail.local

# Enable and start Fail2Ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Step 4: Regular Security Updates

```bash
# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Check update status
sudo unattended-upgrades --dry-run --debug
```

### Step 5: Backup Configuration

Create a backup script for configuration:

```bash
vim scripts/backup_config.sh
```

Add the following content:

```bash
#!/bin/bash

# Backup configuration files

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

echo "✅ Configuration backup completed: $BACKUP_FILE"
```

Make it executable:

```bash
chmod +x scripts/backup_config.sh
```

---

## Troubleshooting

### Issue: Bot Not Starting

**Symptoms**: Bot fails to start or crashes immediately

**Solutions**:

1. Check logs:
   ```bash
   tail -50 logs/bot.log
   ```

2. Verify configuration:
   ```bash
   cat config/.env
   ```

3. Test Python environment:
   ```bash
   python3 -m src.bot.bot
   ```

4. Check dependencies:
   ```bash
   pip list
   ```

### Issue: Sync Process Fails

**Symptoms**: Sync process fails with errors

**Solutions**:

1. Check sync logs:
   ```bash
   cat logs/sync_10am.log
   ```

2. Test Dropbox connection:
   ```bash
   python3 -c "from src.data.downloader import DropboxDownloader; from src.core.config import load_config; config = load_config(); downloader = DropboxDownloader(config.dropbox); print(downloader.list_backups())"
   ```

3. Verify database connection:
   ```bash
   docker exec -u postgres pg-i5bu psql -U postgres -c "SELECT 1;"
   ```

4. Check disk space:
   ```bash
   df -h
   ```

### Issue: PostgreSQL Container Not Starting

**Symptoms**: Database container fails to start

**Solutions**:

1. Check Docker logs:
   ```bash
   docker logs pg-i5bu
   ```

2. Restart container:
   ```bash
   docker-compose -f docker/docker-compose.yml restart
   ```

3. Check port conflicts:
   ```bash
   netstat -tlnp | grep 5432
   ```

4. Verify Docker is running:
   ```bash
   systemctl status docker
   ```

### Issue: Cron Jobs Not Running

**Symptoms**: Scheduled tasks don't execute

**Solutions**:

1. Check cron service:
   ```bash
   systemctl status cron
   ```

2. Verify cron jobs:
   ```bash
   crontab -l
   ```

3. Check cron logs:
   ```bash
   sudo tail -f /var/log/syslog | grep CRON
   ```

4. Test cron command manually:
   ```bash
   cd /home/telegrambot/telegram-bot-toko && /home/telegrambot/telegram-bot-toko/venv/bin/python scripts/sync.py
   ```

### Issue: High Disk Usage

**Symptoms**: Server runs out of disk space

**Solutions**:

1. Check disk usage:
   ```bash
   df -h
   du -sh /home/telegrambot/telegram-bot-toko/*
   ```

2. Clean old backups:
   ```bash
   find data/backups -name "*.i5bu" -mtime +7 -delete
   ```

3. Clean old logs:
   ```bash
   find logs -name "*.log" -mtime +30 -delete
   ```

4. Clean Docker resources:
   ```bash
   docker system prune -a
   ```

### Issue: Telegram Bot Not Responding

**Symptoms**: Bot doesn't respond to messages

**Solutions**:

1. Check if bot is running:
   ```bash
   ps aux | grep bot.py
   ```

2. Check bot logs:
   ```bash
   tail -f logs/bot.log
   ```

3. Test bot token:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

4. Restart bot:
   ```bash
   pkill -f bot.py
   nohup python3 -m src.bot.bot > logs/bot.log 2>&1 &
   ```

---

## Additional Resources

### Documentation

- [Main README](../README.md) - Project overview
- [Architecture](ARCHITECTURE.md) - System architecture
- [Components](COMPONENTS.md) - Component diagrams
- [Migration Complete](MIGRATION_COMPLETE.md) - Migration status

### Useful Commands

```bash
# Quick status check
./scripts/health_check.sh

# Full monitoring report
./scripts/monitor.sh

# Manual backup
./scripts/backup.sh

# Run sync
python scripts/sync.py

# Run tests
pytest tests/ -v

# View Docker logs
docker logs pg-i5bu --tail 100 -f

# Check cron jobs
crontab -l

# View recent logs
tail -f logs/sync_10am.log
```

### Support

For issues or questions:
1. Check this deployment guide
2. Review logs in `logs/` directory
3. Run health check: `./scripts/health_check.sh`
4. Run tests: `pytest tests/ -v`
5. Check [troubleshooting section](#troubleshooting)

---

**Deployment Guide Version**: 1.0.0
**Last Updated**: 2025-01-04
**Compatible With**: Telegram Bot Toko v2.0.0
