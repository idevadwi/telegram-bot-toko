# Quick Start Deployment Guide - Telegram Bot Toko

This is a condensed version of the full deployment guide for quick reference. For detailed instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

## 🚀 Quick Deployment Steps

### 1. Server Setup (5 minutes)

**Note**: This guide has been tested on Ubuntu 20.04, 22.04, and 24.04 LTS.

```bash
# Connect to VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create user
adduser telegrambot
usermod -aG sudo telegrambot
usermod -aG docker telegrambot
su - telegrambot
```

### 2. Project Setup (3 minutes)

```bash
# Clone repository
cd ~
git clone <your-repo-url> telegram-bot-toko
cd telegram-bot-toko

# Create directories
mkdir -p data/backups data/exports logs backups/manual

# Install Python dependencies (requires virtual environment on newer Ubuntu)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh
```

### 3. Configuration (5 minutes)

```bash
# Create environment file
cp config/.env.example config/.env
vim config/.env
```

**Required Configuration:**

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id

# Dropbox
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
DROPBOX_FOLDER_PATH=/IPOS

# Database
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=your_password

# Paths (update to match your setup)
PROJECT_ROOT=/home/telegrambot/telegram-bot-toko
DATA_DIR=/home/telegrambot/telegram-bot-toko/data
BACKUPS_DIR=/home/telegrambot/telegram-bot-toko/data/backups
EXPORTS_DIR=/home/telegrambot/telegram-bot-toko/data/exports
LOGS_DIR=/home/telegrambot/telegram-bot-toko/logs
```

**Secure the file:**
```bash
chmod 600 config/.env
```

### 4. Start Database (1 minute)

```bash
# Start PostgreSQL container
docker-compose -f docker/docker-compose.yml up -d

# Verify it's running
docker ps | grep pg-i5bu
```

### 5. Test System (2 minutes)

```bash
# Run sync process (must run as module from project root)
python -m scripts.sync

# Run health check
./scripts/health_check.sh

# Run monitoring
./scripts/monitor.sh
```

### 6. Start Bot (1 minute)

```bash
# Test bot in foreground
python -m src.bot.bot

# Or run in background
nohup python -m src.bot.bot > logs/bot.log 2>&1 &
```

### 7. Setup Automation (2 minutes)

```bash
# Edit crontab
crontab -e
```

**Add these cron jobs:**

```bash
# Sync at 10:00 AM and 7:00 PM daily
0 10 * * * cd /home/telegrambot/telegram-bot-toko && /home/telegrambot/telegram-bot-toko/venv/bin/python -m scripts.sync >> logs/sync_10am.log 2>&1
0 19 * * * cd /home/telegrambot/telegram-bot-toko && /home/telegrambot/telegram-bot-toko/venv/bin/python -m scripts.sync >> logs/sync_7pm.log 2>&1

# Health check every hour
0 * * * * cd /home/telegrambot/telegram-bot-toko && ./scripts/health_check.sh >> logs/health.log 2>&1

# Backup daily at 11:00 PM
0 23 * * * cd /home/telegrambot/telegram-bot-toko && ./scripts/backup.sh >> logs/backup.log 2>&1
```

## 📋 Getting Credentials

### Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow instructions and copy the token

### Admin Chat ID

1. Start a conversation with your bot
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find your `chat_id` in the response

### Dropbox Credentials

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create a new app with scoped access
3. Get App Key and App Secret
4. Generate a refresh token using the OAuth2 playground

## 🔧 Useful Commands

```bash
# Quick status
./scripts/health_check.sh

# Full monitoring
./scripts/monitor.sh

# Manual backup
./scripts/backup.sh

# Run sync (must run as module from project root)
python -m scripts.sync

# View logs
tail -f logs/sync_10am.log

# Check Docker
docker ps
docker logs pg-i5bu

# View cron jobs
crontab -l
```

## 🐛 Troubleshooting

### Bot not responding
```bash
# Check if running
ps aux | grep bot.py

# View logs
tail -f logs/bot.log

# Restart
pkill -f bot.py
nohup python -m src.bot.bot > logs/bot.log 2>&1 &
```

### Sync failing
```bash
# Check logs
cat logs/sync_10am.log

# Test manually
python -m scripts.sync

# Check disk space
df -h
```

### Database issues
```bash
# Check container
docker ps | grep pg-i5bu

# View logs
docker logs pg-i5bu

# Restart
docker-compose -f docker/docker-compose.yml restart
```

## 📊 Monitoring

### Check system status
```bash
./scripts/monitor.sh
```

### View recent logs
```bash
# Sync logs
tail -20 logs/sync_10am.log

# Health logs
tail -20 logs/health.log

# Bot logs
tail -20 logs/bot.log
```

### Check resources
```bash
# Disk usage
df -h

# Memory usage
free -h

# Docker stats
docker stats pg-i5bu
```

## 🔒 Security Tips

1. **Use SSH keys** instead of password authentication
2. **Disable root login** in `/etc/ssh/sshd_config`
3. **Keep system updated**: `apt update && apt upgrade -y`
4. **Set up firewall**: `ufw allow 22/tcp`
5. **Use strong passwords** for database and accounts
6. **Never commit** `.env` file to version control
7. **Regular backups**: Use `./scripts/backup.sh`

## 📚 Additional Resources

- **Full Deployment Guide**: [`DEPLOYMENT.md`](DEPLOYMENT.md)
- **Main README**: [`../README.md`](../README.md)
- **Architecture**: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- **Components**: [`COMPONENTS.md`](COMPONENTS.md)

## ✅ Deployment Checklist

- [ ] Server updated and Docker installed
- [ ] Repository cloned and dependencies installed
- [ ] Environment file configured with all credentials
- [ ] PostgreSQL container running
- [ ] Sync process tested successfully
- [ ] Bot tested and responding
- [ ] Cron jobs configured
- [ ] Health check running
- [ ] Log rotation set up
- [ ] Security hardening completed

---

**Estimated Total Time**: 20-30 minutes
**Difficulty**: Intermediate
**Requirements**: Linux VPS, basic command-line knowledge

For detailed troubleshooting and advanced configuration, see the full [`DEPLOYMENT.md`](DEPLOYMENT.md) guide.
