# Phase 7: Telegram Bot Toko Deployment

## Overview
This document covers the deployment of the Telegram Bot Toko system to your VPS. This system automatically syncs IPOS 5 database backups from Dropbox and provides a Telegram bot interface for product price lookups.

**Prerequisites**: 
- Completed Phase 1 (Initial Server Setup)
- Completed Phase 3 (Docker Installation)
- Completed Phase 4 (Nginx Proxy Manager)
- Completed Phase 5 (Database Setup)
- Completed Phase 6 (Application Environments)

**Estimated Time**: 45-60 minutes

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
│  │   Files      │      │   API        │                 │
│  └──────────────┘      └──────────────┘                 │
│                                                            │
│  Networks: bot-network, db-network, proxy-network           │
└─────────────────────────────────────────────────────────────┘
```

---

## Part A: VPS Preparation

### Step 1: Create Project Directory

```bash
# SSH into your VPS
ssh deploy@YOUR_VPS_IP

# Create project directory
mkdir -p ~/apps/telegram-bot-toko

# Navigate to directory
cd ~/apps/telegram-bot-toko
```

---

### Step 2: Clone Repository

```bash
# Clone your repository (replace with your actual repository URL)
git clone https://github.com/YOUR_USERNAME/telegram-bot-toko.git .

# Verify files are present
ls -la
```

**Expected output**:
```
config/
data/
docker/
logs/
scripts/
src/
tests/
Makefile
README.md
requirements.txt
```

---

### Step 3: Create Required Directories

```bash
# Create data directories
mkdir -p data/backups
mkdir -p data/exports
mkdir -p logs

# Set proper permissions
chmod -R 755 data
chmod -R 755 logs
```

---

### Step 4: Configure Environment Variables

```bash
# Copy example environment file
cp config/.env.example config/.env

# Edit environment file
nano config/.env
```

Update the configuration with your actual values:

```bash
# Dropbox Configuration
DROPBOX_APP_KEY=your_actual_app_key
DROPBOX_APP_SECRET=your_actual_app_secret
DROPBOX_REFRESH_TOKEN=your_actual_refresh_token
DROPBOX_FOLDER_PATH=/IPOS

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_actual_bot_token
ALLOWED_USERS=123456789,987654321

# Database Configuration
DB_HOST=postgresql-server
DB_PORT=5432
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=your_postgres_password_from_phase5

# Application Configuration
MAX_CSV_FILES=5
SEARCH_RESULTS_LIMIT=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Important Notes**:
- Use the PostgreSQL password you generated in Phase 5
- Get your Telegram bot token from [@BotFather](https://t.me/botfather)
- Get Dropbox credentials from [Dropbox Developer Console](https://www.dropbox.com/developers)
- ALLOWED_USERS should contain Telegram user IDs (comma-separated)

---

## Part B: Database Setup for i5bu

### Step 1: Create i5bu Database

```bash
# Connect to PostgreSQL
docker exec -it postgresql-server psql -U postgres
```

Run these SQL commands:

```sql
-- Create i5bu database
CREATE DATABASE i5bu;

-- Create user for the bot (optional, if you want separate user)
CREATE USER telegram_bot WITH ENCRYPTED PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE i5bu TO telegram_bot;

-- Exit
\q
```

---

### Step 2: Verify Database Connection

```bash
# Test connection from VPS
docker exec -it postgresql-server psql -U postgres -d i5bu -c "SELECT version();"
```

**Expected output**: PostgreSQL version information

---

### Step 3: Prepare Database Schema

The i5bu database will be populated automatically when you restore `.i5bu` backup files. The expected schema includes:

- `tbl_item` - Product items
- `tbl_itemsatuanjml` - Item units and quantities
- `tbl_itemhj` - Item selling prices

---

## Part C: Docker Deployment

### Step 1: Review Docker Configuration

Check the existing [`docker-compose.yml`](docker-compose.yml):

```bash
cat docker/docker-compose.yml
```

The configuration should match this structure:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: pg-i5bu
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: i5bu
    volumes:
      - ../data/backups:/backup:ro
      - ../data/exports:/output
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - bot-network

  bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: telegram-bot-toko
    env_file:
      - ../config/.env
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - bot-network

volumes:
  pgdata:

networks:
  bot-network:
    driver: bridge
```

---

### Step 2: Update Docker Compose for VPS

Modify the docker-compose.yml to use the external PostgreSQL from Phase 5:

```bash
# Navigate to docker directory
cd ~/apps/telegram-bot-toko/docker

# Edit docker-compose.yml
nano docker-compose.yml
```

Replace with this VPS-optimized configuration:

```yaml
services:
  bot:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: telegram-bot-toko
    env_file:
      - ../config/.env
    volumes:
      - ../data:/app/data
      - ../logs:/app/logs
    networks:
      - db-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import sys; sys.exit(0)'"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    security_opt:
      - no-new-privileges:true

networks:
  db-network:
    external: true
    name: db-network
```

**Changes made**:
- Removed local PostgreSQL service (using external from Phase 5)
- Connected to `db-network` (external network from Phase 3)
- Added healthcheck for the bot
- Added logging configuration
- Added security options

---

### Step 3: Build Docker Image

```bash
# Navigate to docker directory
cd ~/apps/telegram-bot-toko/docker

# Build the bot image (includes scripts directory with sync script)
docker compose build

# Verify image was built
docker images | grep telegram-bot-toko
```

**Note**: The Dockerfile now includes the `scripts/` directory, which contains the sync script. This allows running sync commands inside the Docker container where all Python dependencies are installed. The sync script uses direct database connections via psycopg2 instead of docker exec commands, making it work properly inside the container.

---

### Step 4: Start the Bot Container

```bash
# Start the bot
docker compose up -d

# Check if container is running
docker compose ps

# View logs to verify startup
docker compose logs -f
```

**Expected log output**:
```
INFO - Bot is running...
INFO - Reloaded CSV: /app/data/exports/...
```

---

### Step 5: Verify Bot is Working

```bash
# Check container status
docker ps | grep telegram-bot-toko

# Check logs for errors
docker logs telegram-bot-toko --tail=50

# Test bot in Telegram
# Send /start command to your bot
```

---

## Part D: Initial Data Sync

### Step 1: Upload Initial Backup File

If you have an existing `.i5bu` backup file:

```bash
# Upload to VPS (from your local machine)
scp /path/to/your/backup.i5bu deploy@YOUR_VPS_IP:~/apps/telegram-bot-toko/data/backups/

# Or use rsync
rsync -avz /path/to/your/backup.i5bu deploy@YOUR_VPS_IP:~/apps/telegram-bot-toko/data/backups/
```

---

### Step 2: Run Manual Sync

```bash
# Navigate to project directory
cd ~/apps/telegram-bot-toko

# Run sync script inside Docker container (has all dependencies installed)
docker exec -it telegram-bot-toko python -m scripts.sync
```

This will:
1. Download latest backup from Dropbox (if configured)
2. Validate the backup file
3. Restore to PostgreSQL database (via direct psycopg2 connection)
4. Export product data to CSV (via psycopg2 and pandas)
5. Validate CSV file
6. Clean up old files

**Note**: The sync script now uses direct database connections via psycopg2 instead of docker exec commands, allowing it to run properly inside the Docker container. The bot container connects to PostgreSQL via the `db-network`.

---

### Step 3: Verify CSV Export

```bash
# Check if CSV was created
ls -lh data/exports/

# View CSV content (first few lines)
head -20 data/exports/*.csv
```

---

### Step 4: Reload Bot Data

```bash
# Restart bot to load new CSV
docker compose restart bot

# Check logs
docker compose logs -f bot
```

---

## Part E: Automation Setup

### Step 1: Create Sync Script Wrapper

```bash
# Create sync script
nano ~/scripts/sync-telegram-bot.sh
```

Add this content:

```bash
#!/bin/bash
# Telegram Bot sync script wrapper

PROJECT_DIR="$HOME/apps/telegram-bot-toko"
LOG_FILE="$HOME/logs/sync.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

cd "$PROJECT_DIR" || exit 1

echo "[$DATE] Starting sync..." >> "$LOG_FILE"

# Run sync inside Docker container (has all dependencies installed)
docker exec telegram-bot-toko python -m scripts.sync >> "$LOG_FILE" 2>&1

# Check if sync was successful
if [ $? -eq 0 ]; then
    echo "[$DATE] Sync completed successfully" >> "$LOG_FILE"
    
    # Reload bot data
    echo "[$DATE] Reloading bot..." >> "$LOG_FILE"
    cd docker
    docker compose restart bot
else
    echo "[$DATE] Sync failed!" >> "$LOG_FILE"
fi
```

Make executable:

```bash
chmod +x ~/scripts/sync-telegram-bot.sh
```

---

### Step 2: Set Up Cron Jobs

```bash
# Edit crontab
crontab -e
```

Add these entries:

```bash
# Toko Sync at 10:00 AM daily
0 10 * * * /home/deploy/scripts/sync-telegram-bot.sh >> /home/deploy/logs/cron_sync.log 2>&1

# Toko Sync at 7:00 PM daily
0 19 * * * /home/deploy/scripts/sync-telegram-bot.sh >> /home/deploy/logs/cron_sync.log 2>&1

# Health check every hour
0 * * * * /home/deploy/apps/telegram-bot-toko/scripts/health_check.sh >> /home/deploy/logs/cron_health.log 2>&1

# Backup configuration daily at 11:00 PM
0 23 * * * /home/deploy/apps/telegram-bot-toko/scripts/backup.sh >> /home/deploy/logs/cron_backup.log 2>&1
```

---

### Step 3: Verify Cron Jobs

```bash
# List cron jobs
crontab -l

# Check if jobs are scheduled
# Wait for next scheduled time and check logs
tail -f ~/logs/sync.log
```

---

## Part F: Monitoring and Maintenance

### Step 1: Create Monitoring Script

```bash
nano ~/scripts/monitor-telegram-bot.sh
```

Add this content:

```bash
#!/bin/bash
# Telegram Bot monitoring script

PROJECT_DIR="$HOME/apps/telegram-bot-toko"
BOT_CONTAINER="telegram-bot-toko"
DB_CONTAINER="postgresql-server"

echo "=== Telegram Bot Toko Status ==="
echo ""

# Check bot container
echo "Bot Container Status:"
docker ps -f name=$BOT_CONTAINER --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check database container
echo "Database Container Status:"
docker ps -f name=$DB_CONTAINER --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check disk usage
echo "Disk Usage:"
df -h | grep -E '/$|/home'
echo ""

# Check latest CSV file
echo "Latest CSV File:"
ls -lht "$PROJECT_DIR/data/exports/" | head -2
echo ""

# Check latest backup file
echo "Latest Backup File:"
ls -lht "$PROJECT_DIR/data/backups/" | head -2
echo ""

# Check bot logs (last 10 lines)
echo "Recent Bot Logs:"
docker logs $BOT_CONTAINER --tail=10
echo ""

# Check sync logs (last 10 lines)
echo "Recent Sync Logs:"
tail -10 "$HOME/logs/sync.log" 2>/dev/null || echo "No sync logs yet"
```

Make executable:

```bash
chmod +x ~/scripts/monitor-telegram-bot.sh
```

---

### Step 2: Run Monitoring Script

```bash
# Run monitoring script
~/scripts/monitor-telegram-bot.sh
```

---

### Step 3: Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/telegram-bot
```

Add this configuration:

```
/home/deploy/apps/telegram-bot-toko/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 deploy deploy
}

/home/deploy/logs/sync.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 deploy deploy
}
```

Test logrotate:

```bash
sudo logrotate -f /etc/logrotate.d/telegram-bot
```

---

## Part G: Backup Strategy

### Step 1: Create Backup Script

```bash
nano ~/scripts/backup-telegram-bot.sh
```

Add this content:

```bash
#!/bin/bash
# Telegram Bot backup script

PROJECT_DIR="$HOME/apps/telegram-bot-toko"
BACKUP_DIR="$HOME/backups/telegram-bot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "Creating backup..."

# Backup configuration
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$PROJECT_DIR" config/

# Backup CSV exports
tar czf "$BACKUP_DIR/exports_$DATE.tar.gz" -C "$PROJECT_DIR" data/exports/

# Backup logs
tar czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$PROJECT_DIR" logs/

# Backup database
docker exec postgresql-server pg_dump -U postgres i5bu | gzip > "$BACKUP_DIR/database_$DATE.sql.gz"

echo "Backup complete: $BACKUP_DIR"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# Show backup size
du -sh "$BACKUP_DIR"
```

Make executable:

```bash
chmod +x ~/scripts/backup-telegram-bot.sh
```

---

### Step 2: Test Backup Script

```bash
# Run backup script
~/scripts/backup-telegram-bot.sh

# Verify backups were created
ls -lh ~/backups/telegram-bot/
```

---

## Part H: Security Considerations

### Step 1: Secure Environment File

```bash
# Set restrictive permissions on .env file
chmod 600 ~/apps/telegram-bot-toko/config/.env

# Verify permissions
ls -la ~/apps/telegram-bot-toko/config/
```

---

### Step 2: Restrict Bot Access

The bot already has `ALLOWED_USERS` configuration. To add more users:

1. Get Telegram user ID:
   - Send a message to [@userinfobot](https://t.me/userinfobot)
   - Note your ID

2. Update `.env` file:
```bash
nano ~/apps/telegram-bot-toko/config/.env
```

Add comma-separated user IDs:
```bash
ALLOWED_USERS=123456789,987654321,555666777
```

3. Restart bot:
```bash
cd ~/apps/telegram-bot-toko/docker
docker compose restart bot
```

---

### Step 3: Secure Dropbox Credentials

Ensure Dropbox credentials are not exposed:

```bash
# Check .env is in .gitignore
cat ~/apps/telegram-bot-toko/.gitignore | grep .env

# Verify no credentials in logs
grep -r "DROPBOX" ~/apps/telegram-bot-toko/logs/
```

---

## Part I: Troubleshooting

### Issue 1: Bot Not Starting

**Symptoms**: Container exits immediately or fails to start

**Solutions**:

```bash
# Check container logs
docker logs telegram-bot-toko

# Check if CSV files exist
ls -la ~/apps/telegram-bot-toko/data/exports/

# Check environment file
cat ~/apps/telegram-bot-toko/config/.env

# Rebuild container
cd ~/apps/telegram-bot-toko/docker
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

### Issue 2: Database Connection Failed

**Symptoms**: Bot can't connect to PostgreSQL

**Solutions**:

```bash
# Check if PostgreSQL is running
docker ps | grep postgresql-server

# Test database connection
docker exec -it postgresql-server psql -U postgres -d i5bu -c "SELECT 1;"

# Check network connectivity
docker network inspect db-network

# Verify DB_HOST in .env
grep DB_HOST ~/apps/telegram-bot-toko/config/.env
```

---

### Issue 3: Sync Process Fails

**Symptoms**: Sync script fails to download or process backup

**Solutions**:

```bash
# Check sync logs
tail -50 ~/logs/sync.log

# Verify Dropbox credentials
grep DROPBOX ~/apps/telegram-bot-toko/config/.env

# Test Dropbox connection manually
cd ~/apps/telegram-bot-toko
python -c "from src.data.downloader import DropboxDownloader; print('Dropbox OK')"

# Check backup file exists
ls -lh ~/apps/telegram-bot-toko/data/backups/
```

---

### Issue 4: Bot Not Responding to Commands

**Symptoms**: Bot doesn't respond to /start, /reload, or search queries

**Solutions**:

```bash
# Check bot logs for errors
docker logs telegram-bot-toko --tail=100

# Verify bot token is correct
grep TELEGRAM_BOT_TOKEN ~/apps/telegram-bot-toko/config/.env

# Test bot token (from local machine)
curl https://api.telegram.org/botYOUR_TOKEN/getMe

# Restart bot
cd ~/apps/telegram-bot-toko/docker
docker compose restart bot
```

---

### Issue 5: CSV File Not Found

**Symptoms**: Bot reports "Tidak ada file CSV ditemukan"

**Solutions**:

```bash
# Check exports directory
ls -la ~/apps/telegram-bot-toko/data/exports/

# Run sync manually to generate CSV
cd ~/apps/telegram-bot-toko
docker exec -it telegram-bot-toko python -m scripts.sync

# Check sync logs for errors
tail -50 ~/logs/sync.log

# Verify CSV format
head -5 ~/apps/telegram-bot-toko/data/exports/*.csv
```

---

### Issue 6: ModuleNotFoundError When Running Sync

**Symptoms**: Running `python -m scripts.sync` on VPS host fails with:
```
ModuleNotFoundError: No module named 'dotenv'
```

**Root Cause**: The sync script is being run directly on the VPS host system where Python dependencies (like `python-dotenv`) aren't installed. The Docker container has all dependencies installed, but the scripts directory wasn't copied into the container.

**Solutions**:

```bash
# 1. Verify scripts directory is in Docker container
docker exec telegram-bot-toko ls -la /app/scripts/

# If scripts directory doesn't exist, rebuild the container:
cd ~/apps/telegram-bot-toko/docker
docker compose down
docker compose build --no-cache
docker compose up -d

# 2. Run sync inside Docker container (recommended)
docker exec -it telegram-bot-toko python -m scripts.sync

# 3. Alternative: Install dependencies on host (not recommended)
cd ~/apps/telegram-bot-toko
pip install -r requirements.txt
python -m scripts.sync
```

**Prevention**: Always run sync commands inside the Docker container to ensure consistent environment and avoid dependency issues.

---

### Issue 7: Docker Command Not Found Inside Container

**Symptoms**: Running sync inside Docker container fails with:
```
FileNotFoundError: [Errno 2] No such file or directory: 'docker'
```

**Root Cause**: The sync script was trying to run `docker exec` commands from inside the Docker container, but Docker isn't installed inside containers. The bot container should connect directly to PostgreSQL via the `db-network` instead.

**Solution**: The code has been updated to use direct database connections via psycopg2 instead of docker exec commands. Ensure you have the latest version of the code:

```bash
# Pull latest changes
cd ~/apps/telegram-bot-toko
git pull origin main

# Rebuild container with updated code
cd docker
docker compose down
docker compose build --no-cache
docker compose up -d

# Test sync
docker exec -it telegram-bot-toko python -m scripts.sync
```

**Technical Details**:
- `ensure_database_running()` now uses psycopg2.connect() to test database connectivity
- `restore_database()` uses dropdb/createdb/pg_restore directly (requires postgresql-client in container)
- `export_to_csv()` uses psycopg2 and pandas read_sql_query directly

**Note**: The Dockerfile already includes `postgresql-client` which provides the necessary PostgreSQL command-line tools.

---

## Part J: Performance Optimization

### Step 1: Optimize Database Queries

The bot uses pandas for CSV searches. For large datasets:

```bash
# Edit config to limit results
nano ~/apps/telegram-bot-toko/config/.env
```

Set:
```bash
SEARCH_RESULTS_LIMIT=10
```

---

### Step 2: Optimize PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it postgresql-server psql -U postgres -d i5bu
```

Run optimization commands:

```sql
-- Analyze tables for query optimization
ANALYZE tbl_item;
ANALYZE tbl_itemsatuanjml;
ANALYZE tbl_itemhj;

-- Create indexes if needed
CREATE INDEX IF NOT EXISTS idx_item_name ON tbl_item(namaitem);
CREATE INDEX IF NOT EXISTS idx_item_code ON tbl_item(kodeitem);

-- Exit
\q
```

---

### Step 3: Monitor Resource Usage

```bash
# Check container resource usage
docker stats telegram-bot-toko postgresql-server --no-stream

# Check system resources
htop
```

---

## Part K: Verification Checklist

Run these commands to verify your deployment:

```bash
# 1. Check containers are running
docker ps | grep -E "telegram-bot-toko|postgresql-server"

# 2. Check bot logs
docker logs telegram-bot-toko --tail=20

# 3. Test database connection
docker exec postgresql-server pg_isready -U postgres

# 4. Check CSV files exist
ls -lh ~/apps/telegram-bot-toko/data/exports/

# 5. Test bot in Telegram
# Send /start command to your bot

# 6. Check cron jobs
crontab -l

# 7. Check monitoring script
~/scripts/monitor-telegram-bot.sh

# 8. Check backups
ls -lh ~/backups/telegram-bot/

# 9. Check logs
tail -20 ~/logs/sync.log
```

---

## Part L: Next Steps

### Optional: Set Up Nginx Proxy Manager

If you want to expose a web interface or API:

1. Access Nginx Proxy Manager at `http://YOUR_VPS_IP:81`
2. Add a proxy host for your domain
3. Configure SSL certificate

### Optional: Set Up Monitoring Dashboard

Deploy monitoring tools like:
- Grafana + Prometheus for metrics
- cAdvisor for container monitoring
- Custom health check dashboard

### Optional: Set Up Alerts

Configure alerts for:
- Bot container failures
- Sync failures
- Database connection issues
- Disk space warnings

---

## Part M: Maintenance Commands

### Daily Commands

```bash
# Check bot status
docker ps | grep telegram-bot-toko

# Check recent logs
docker logs telegram-bot-toko --tail=50

# Check sync status
tail -20 ~/logs/sync.log
```

### Weekly Commands

```bash
# Run full monitoring
~/scripts/monitor-telegram-bot.sh

# Check disk usage
df -h

# Clean up old logs
find ~/logs -name "*.log" -mtime +30 -delete

# Review backups
ls -lh ~/backups/telegram-bot/
```

### Monthly Commands

```bash
# Update bot code
cd ~/apps/telegram-bot-toko
git pull origin main

# Rebuild container
cd docker
docker compose down
docker compose build --no-cache
docker compose up -d

# Test all functionality
docker exec -it telegram-bot-toko python -m scripts.sync
```

---

## Part N: Emergency Procedures

### Restore from Backup

```bash
# Restore configuration
cd ~/apps/telegram-bot-toko
tar xzf ~/backups/telegram-bot/config_YYYYMMDD_HHMMSS.tar.gz -C ./

# Restore CSV exports
tar xzf ~/backups/telegram-bot/exports_YYYYMMDD_HHMMSS.tar.gz -C ./

# Restore database
gunzip < ~/backups/telegram-bot/database_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i postgresql-server psql -U postgres -d i5bu

# Restart bot
cd docker
docker compose restart bot
```

### Emergency Stop

```bash
# Stop bot immediately
cd ~/apps/telegram-bot-toko/docker
docker compose down

# Check if stopped
docker ps | grep telegram-bot-toko
```

### Emergency Restart

```bash
# Restart all services
cd ~/apps/telegram-bot-toko/docker
docker compose down
docker compose up -d

# Verify startup
docker compose logs -f
```

---

## Summary

Your Telegram Bot Toko is now deployed on your VPS with:

✅ Docker containerization for bot and database
✅ Automated sync from Dropbox
✅ Telegram bot for product price lookups
✅ Automated daily backups
✅ Health monitoring
✅ Log rotation
✅ Security configurations
✅ Cron job automation

**Key Files**:
- Configuration: `~/apps/telegram-bot-toko/config/.env`
- Logs: `~/apps/telegram-bot-toko/logs/`
- Data: `~/apps/telegram-bot-toko/data/`
- Backups: `~/backups/telegram-bot/`
- Scripts: `~/scripts/`

**Useful Commands**:
- Monitor: `~/scripts/monitor-telegram-bot.sh`
- Sync: `~/scripts/sync-telegram-bot.sh`
- Backup: `~/scripts/backup-telegram-bot.sh`
- Bot logs: `docker logs telegram-bot-toko -f`
- Restart bot: `cd ~/apps/telegram-bot-toko/docker && docker compose restart`

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-12  
**Tested On**: Ubuntu 24.04 LTS with Docker 24.x
