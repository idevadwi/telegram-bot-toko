# Telegram Bot Toko - Deployment Summary

## Quick Overview

This document provides a quick reference guide for deploying and managing the Telegram Bot Toko system on your VPS.

**Deployment Status**: Phase 7 (Ready for Execution)  
**Estimated Time**: 45-60 minutes  
**Prerequisites**: Phases 1-6 completed (Initial Setup, Docker, Nginx Proxy Manager, Database, Application Environments)

---

## Deployment Checklist

### Pre-Deployment Checklist

- [x] Phase 1: Initial Server Setup completed
- [x] Phase 3: Docker Installation completed
- [x] Phase 4: Nginx Proxy Manager installed
- [x] Phase 5: PostgreSQL database setup completed
- [x] Phase 6: Application environments configured
- [ ] Phase 7A: Manual deployment completed
- [ ] Phase 7B: CI/CD GitHub Actions configured

---

## Deployment Documents

### 1. Main Deployment Guide
**File**: [`07-TELEGRAM-BOT-DEPLOYMENT.md`](07-TELEGRAM-BOT-DEPLOYMENT.md)

**Contents**:
- VPS preparation and project setup
- Database configuration for i5bu
- Docker deployment steps
- Environment configuration
- Automation setup (cron jobs)
- Monitoring and maintenance
- Security considerations
- Troubleshooting guide
- Emergency procedures

**When to use**: First-time deployment, manual updates, troubleshooting

---

### 2. CI/CD Workflow Guide
**File**: [`TELEGRAM-BOT-CICD-WORKFLOW.md`](TELEGRAM-BOT-CICD-WORKFLOW.md)

**Contents**:
- GitHub Actions workflow configuration
- Required GitHub secrets
- Automated deployment on push
- Manual workflow triggers (deploy, sync, restart)
- Testing and verification
- Troubleshooting CI/CD issues

**When to use**: Setting up automated deployments, configuring GitHub Actions

---

## Quick Start Guide

### Option 1: Manual Deployment (Recommended for First-Time)

Follow these steps from [`07-TELEGRAM-BOT-DEPLOYMENT.md`](07-TELEGRAM-BOT-DEPLOYMENT.md):

```bash
# 1. SSH into VPS
ssh deploy@YOUR_VPS_IP

# 2. Create project directory
mkdir -p ~/apps/telegram-bot-toko
cd ~/apps/telegram-bot-toko

# 3. Clone repository
git clone https://github.com/YOUR_USERNAME/telegram-bot-toko.git .

# 4. Create directories
mkdir -p data/backups data/exports logs

# 5. Configure environment
cp config/.env.example config/.env
nano config/.env
# Update with your actual values

# 6. Create i5bu database
docker exec -it postgresql-server psql -U postgres
CREATE DATABASE i5bu;
\q

# 7. Update docker-compose.yml for VPS
cd docker
nano docker-compose.yml
# Use configuration from deployment guide

# 8. Build and start
docker compose build
docker compose up -d

# 9. Verify deployment
docker compose ps
docker compose logs -f
```

---

### Option 2: CI/CD Automated Deployment

Follow these steps from [`TELEGRAM-BOT-CICD-WORKFLOW.md`](TELEGRAM-BOT-CICD-WORKFLOW.md):

```bash
# 1. Create workflow file locally
mkdir -p .github/workflows
nano .github/workflows/deploy-telegram-bot-toko.yml
# Paste workflow content from CI/CD guide

# 2. Commit and push
git add .github/workflows/deploy-telegram-bot-toko.yml
git commit -m "Add CI/CD workflow"
git push origin main

# 3. Configure GitHub Secrets
# Go to GitHub → Settings → Secrets and variables → Actions
# Add all required secrets (see CI/CD guide)

# 4. Test deployment
# Make a small change and push to trigger deployment
```

---

## Required Credentials

### Before You Start, Gather These:

#### 1. Telegram Bot Credentials
- **Bot Token**: From [@BotFather](https://t.me/botfather)
- **Allowed User IDs**: From [@userinfobot](https://t.me/userinfobot)

#### 2. Dropbox Credentials
- **App Key**: From [Dropbox Developer Console](https://www.dropbox.com/developers)
- **App Secret**: From Dropbox Developer Console
- **Refresh Token**: From Dropbox Developer Console

#### 3. Database Credentials
- **PostgreSQL Password**: Generated in Phase 5
- **Database Name**: `i5bu`
- **Database User**: `postgres`

#### 4. VPS Credentials
- **VPS IP Address**: Your server IP
- **SSH Username**: `deploy`
- **SSH Private Key**: Generated in Phase 7 (vps_docs/07-CICD-GITHUB-ACTIONS.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS Server                             │
│                                                            │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │  Telegram    │      │  PostgreSQL  │                 │
│  │    Bot       │──────│   Container  │                 │
│  │  Container   │      │    (i5bu)    │                 │
│  └──────────────┘      └──────────────┘                 │
│         │                      │                            │
│         │                      │                            │
│         ▼                      ▼                            │
│  ┌──────────────┐      ┌──────────────┐                 │
│  │    CSV       │      │   Dropbox    │                 │
│  │   Files      │◀─────│   API        │                 │
│  └──────────────┘      └──────────────┘                 │
│                                                            │
│  Networks: bot-network, db-network, proxy-network           │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Configuration Files

### 1. Environment Variables
**Location**: `~/apps/telegram-bot-toko/config/.env`

**Critical Settings**:
```bash
# Dropbox Configuration
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
DROPBOX_FOLDER_PATH=/IPOS

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USERS=123456789,987654321

# Database Configuration
DB_HOST=postgresql-server
DB_PORT=5432
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=your_postgres_password

# Application Configuration
MAX_CSV_FILES=5
SEARCH_RESULTS_LIMIT=10
```

### 2. Docker Compose
**Location**: `~/apps/telegram-bot-toko/docker/docker-compose.yml`

**Key Settings**:
- Uses external `db-network` from Phase 3
- Connects to `postgresql-server` from Phase 5
- Health checks for bot container
- Logging configuration
- Security options

---

## Daily Operations

### Check Bot Status
```bash
# Check if container is running
docker ps | grep telegram-bot-toko

# View logs
docker logs telegram-bot-toko --tail=50

# Monitor logs in real-time
docker logs telegram-bot-toko -f
```

### Run Data Sync
```bash
# Manual sync
cd ~/apps/telegram-bot-toko
python -m scripts.sync

# Or use cron job (automated)
# Runs at 10:00 AM and 7:00 PM daily
```

### Monitor System
```bash
# Run monitoring script
~/scripts/monitor-telegram-bot.sh

# Check disk usage
df -h

# Check container resources
docker stats telegram-bot-toko postgresql-server --no-stream
```

### Backup Data
```bash
# Manual backup
~/scripts/backup-telegram-bot.sh

# Or use cron job (automated)
# Runs daily at 11:00 PM
```

---

## Maintenance Schedule

### Daily
- Check bot status: `docker ps | grep telegram-bot-toko`
- Review recent logs: `docker logs telegram-bot-toko --tail=50`
- Monitor sync status: `tail -20 ~/logs/sync.log`

### Weekly
- Run full monitoring: `~/scripts/monitor-telegram-bot.sh`
- Check disk usage: `df -h`
- Review backups: `ls -lh ~/backups/telegram-bot/`
- Clean up old logs: `find ~/logs -name "*.log" -mtime +30 -delete`

### Monthly
- Update bot code: `cd ~/apps/telegram-bot-toko && git pull origin main`
- Rebuild container: `cd docker && docker compose down && docker compose build --no-cache && docker compose up -d`
- Test all functionality: `python -m scripts.sync`
- Review and rotate credentials if needed

---

## Troubleshooting Quick Reference

### Bot Not Responding
```bash
# Check container status
docker ps | grep telegram-bot-toko

# View logs for errors
docker logs telegram-bot-toko --tail=100

# Restart bot
cd ~/apps/telegram-bot-toko/docker
docker compose restart bot

# If still failing, rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
docker ps | grep postgresql-server

# Test connection
docker exec postgresql-server pg_isready -U postgres

# Check database exists
docker exec -it postgresql-server psql -U postgres -c "\l"

# Restart database
docker restart postgresql-server
```

### Sync Process Failed
```bash
# Check sync logs
tail -50 ~/logs/sync.log

# Verify Dropbox credentials
grep DROPBOX ~/apps/telegram-bot-toko/config/.env

# Test Dropbox connection
cd ~/apps/telegram-bot-toko
python -c "from src.data.downloader import DropboxDownloader; print('OK')"

# Run sync manually
python -m scripts.sync
```

### CSV File Not Found
```bash
# Check exports directory
ls -la ~/apps/telegram-bot-toko/data/exports/

# Run sync to generate CSV
cd ~/apps/telegram-bot-toko
python -m scripts.sync

# Verify CSV format
head -5 ~/apps/telegram-bot-toko/data/exports/*.csv

# Reload bot data
cd docker
docker compose restart bot
```

---

## Emergency Procedures

### Emergency Stop
```bash
cd ~/apps/telegram-bot-toko/docker
docker compose down
```

### Emergency Restart
```bash
cd ~/apps/telegram-bot-toko/docker
docker compose down
docker compose up -d
```

### Restore from Backup
```bash
# Restore configuration
cd ~/apps/telegram-bot-toko
tar xzf ~/backups/telegram-bot/config_YYYYMMDD_HHMMSS.tar.gz -C ./

# Restore database
gunzip < ~/backups/telegram-bot/database_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i postgresql-server psql -U postgres -d i5bu

# Restart bot
cd docker
docker compose restart bot
```

---

## Useful Commands Reference

### Docker Commands
```bash
# Build image
docker compose build

# Start containers
docker compose up -d

# Stop containers
docker compose down

# View logs
docker compose logs -f

# Restart specific service
docker compose restart bot

# Check container status
docker compose ps
```

### Git Commands
```bash
# Pull latest code
git pull origin main

# Check status
git status

# View recent commits
git log --oneline -10
```

### PostgreSQL Commands
```bash
# Connect to database
docker exec -it postgresql-server psql -U postgres -d i5bu

# List tables
\dt

# Run query
SELECT * FROM tbl_item LIMIT 10;

# Exit
\q
```

### Monitoring Commands
```bash
# Run health check
~/apps/telegram-bot-toko/scripts/health_check.sh

# Run monitoring script
~/scripts/monitor-telegram-bot.sh

# View system resources
htop
```

---

## File Locations

| File/Directory | Location | Purpose |
|----------------|-----------|---------|
| Project Root | `~/apps/telegram-bot-toko/` | Main project directory |
| Configuration | `~/apps/telegram-bot-toko/config/.env` | Environment variables |
| Data | `~/apps/telegram-bot-toko/data/` | Backup and export files |
| Backups | `~/backups/telegram-bot/` | System backups |
| Logs | `~/apps/telegram-bot-toko/logs/` | Application logs |
| Sync Logs | `~/logs/sync.log` | Sync process logs |
| Scripts | `~/scripts/` | Management scripts |
| Docker Compose | `~/apps/telegram-bot-toko/docker/docker-compose.yml` | Docker configuration |

---

## Security Best Practices

### 1. Protect Sensitive Files
```bash
# Set restrictive permissions on .env
chmod 600 ~/apps/telegram-bot-toko/config/.env

# Verify .env is in .gitignore
cat ~/apps/telegram-bot-toko/.gitignore | grep .env
```

### 2. Rotate Credentials Regularly
- Change Dropbox tokens every 3 months
- Rotate SSH keys every 3 months
- Update GitHub Secrets after rotation
- Update .env file on VPS

### 3. Monitor Access
```bash
# Check failed login attempts
lastb | head -20

# Check successful logins
last | head -20

# Check bot logs for unauthorized access
grep "Unauthorized" ~/apps/telegram-bot-toko/logs/*.log
```

### 4. Keep Software Updated
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
docker compose pull
docker compose up -d --build

# Update bot code
cd ~/apps/telegram-bot-toko
git pull origin main
```

---

## Performance Tips

### 1. Optimize Search Results
```bash
# Edit .env to limit results
nano ~/apps/telegram-bot-toko/config/.env
SEARCH_RESULTS_LIMIT=10
```

### 2. Optimize Database
```bash
# Connect to PostgreSQL
docker exec -it postgresql-server psql -U postgres -d i5bu

# Analyze tables
ANALYZE tbl_item;
ANALYZE tbl_itemsatuanjml;
ANALYZE tbl_itemhj;

# Create indexes
CREATE INDEX idx_item_name ON tbl_item(namaitem);
CREATE INDEX idx_item_code ON tbl_item(kodeitem);
```

### 3. Monitor Resources
```bash
# Check container resource usage
docker stats telegram-bot-toko postgresql-server --no-stream

# Check system resources
htop
```

---

## Next Steps After Deployment

### Immediate Tasks
1. ✅ Verify bot is responding to `/start` command
2. ✅ Test product search functionality
3. ✅ Verify `/reload` command works
4. ✅ Check `/version` command shows correct timestamp
5. ✅ Test manual sync: `python -m scripts.sync`
6. ✅ Verify CSV files are generated correctly

### Short-Term Tasks (Week 1)
1. Set up cron jobs for automated sync
2. Configure log rotation
3. Set up automated backups
4. Test monitoring scripts
5. Verify all cron jobs are running

### Medium-Term Tasks (Month 1)
1. Set up CI/CD GitHub Actions
2. Configure monitoring dashboard
3. Set up alerts for failures
4. Review and optimize performance
5. Document any customizations

### Long-Term Tasks (Ongoing)
1. Regular security audits
2. Credential rotation schedule
3. Performance monitoring
4. Backup verification
5. Update documentation

---

## Support Resources

### Documentation
- **Main Deployment Guide**: [`07-TELEGRAM-BOT-DEPLOYMENT.md`](07-TELEGRAM-BOT-DEPLOYMENT.md)
- **CI/CD Workflow**: [`TELEGRAM-BOT-CICD-WORKFLOW.md`](TELEGRAM-BOT-CICD-WORKFLOW.md)
- **VPS Setup**: [`01-INITIAL-SERVER-SETUP.md`](01-INITIAL-SERVER-SETUP.md)
- **Docker Setup**: [`03-DOCKER-INSTALLATION.md`](03-DOCKER-INSTALLATION.md)
- **Database Setup**: [`05-DATABASE-SETUP.md`](05-DATABASE-SETUP.md)

### Logs
- **Bot Logs**: `~/apps/telegram-bot-toko/logs/`
- **Sync Logs**: `~/logs/sync.log`
- **Cron Logs**: `~/logs/cron_*.log`

### Commands
- **Health Check**: `~/apps/telegram-bot-toko/scripts/health_check.sh`
- **Monitor**: `~/scripts/monitor-telegram-bot.sh`
- **Backup**: `~/scripts/backup-telegram-bot.sh`
- **Sync**: `~/scripts/sync-telegram-bot.sh`

---

## Summary

Your Telegram Bot Toko deployment is ready! Here's what you have:

✅ **Complete deployment documentation** with step-by-step instructions
✅ **CI/CD workflow** for automated deployments
✅ **Monitoring and maintenance procedures**
✅ **Troubleshooting guides** for common issues
✅ **Emergency procedures** for critical situations
✅ **Security best practices** for production environment

**Key Benefits**:
- Automated data sync from Dropbox
- Real-time product price lookups via Telegram
- Docker containerization for easy management
- Automated backups and monitoring
- CI/CD for streamlined deployments
- Comprehensive logging and troubleshooting

**Estimated Deployment Time**: 45-60 minutes  
**Skill Level**: Intermediate (requires Linux, Docker, and Git knowledge)

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-12  
**Status**: Ready for Deployment

---

## Quick Reference Card

```bash
# SSH to VPS
ssh deploy@YOUR_VPS_IP

# Navigate to project
cd ~/apps/telegram-bot-toko

# Check bot status
docker ps | grep telegram-bot-toko

# View logs
docker logs telegram-bot-toko -f

# Run sync
python -m scripts.sync

# Restart bot
cd docker && docker compose restart bot

# Monitor system
~/scripts/monitor-telegram-bot.sh

# Backup data
~/scripts/backup-telegram-bot.sh

# Check health
scripts/health_check.sh
```

---

**Good luck with your deployment! 🚀**
