# Phase 5: Database Setup (MySQL & PostgreSQL)

## Overview
This document covers the secure setup of MySQL (for Laravel applications) and PostgreSQL (for Python Telegram bot) using Docker containers with proper security configurations.

**Prerequisites**: 
- Completed Phase 3 (Docker Installation)
- Docker networks created (db-network, web-network)

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Host                      │
│                                          │
│  ┌────────────┐      ┌──────────────┐  │
│  │  Laravel   │──────│    MySQL     │  │
│  │   Apps     │      │  Container   │  │
│  └────────────┘      └──────────────┘  │
│                                          │
│  ┌────────────┐      ┌──────────────┐  │
│  │  Telegram  │──────│  PostgreSQL  │  │
│  │    Bot     │      │  Container   │  │
│  └────────────┘      └──────────────┘  │
│                                          │
│  Networks: db-network, web-network      │
└─────────────────────────────────────────┘
```

---

## Part A: MySQL Setup for Laravel

### Step 1: Create MySQL Directory

```bash
# Create MySQL directory
mkdir -p ~/docker/mysql

# Navigate to directory
cd ~/docker/mysql
```

---

### Step 2: Create MySQL Docker Compose File

```bash
nano docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: mysql-server
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: "CHANGE_ROOT_PASSWORD"
      MYSQL_ROOT_HOST: "172.%.%.%"
      TZ: "Asia/Makassar"
    volumes:
      - ./data:/var/lib/mysql
      - ./conf:/etc/mysql/conf.d
      - ./init:/docker-entrypoint-initdb.d
      - ./backups:/backups
    networks:
      - db-network
      - web-network
    command: 
      - --default-authentication-plugin=caching_sha2_password
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --max_connections=200
      - --innodb_buffer_pool_size=1G
      - --innodb_log_file_size=256M
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
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
  web-network:
    external: true
```

---

### Step 3: Generate MySQL Root Password

```bash
# Generate secure root password
openssl rand -base64 32
```

Update the password in docker-compose.yml and save it securely.

---

### Step 4: Create MySQL Configuration File

```bash
# Create conf directory
mkdir -p conf

# Create custom MySQL config
nano conf/my.cnf
```

Add this configuration:

```ini
[mysqld]
# Security Settings
skip-name-resolve
skip-symbolic-links
local-infile=0

# Performance Settings
max_connections=200
max_allowed_packet=256M
innodb_buffer_pool_size=1G
innodb_log_file_size=256M
innodb_flush_log_at_trx_commit=2
innodb_flush_method=O_DIRECT

# Character Set
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# Logging
slow_query_log=1
slow_query_log_file=/var/lib/mysql/slow-query.log
long_query_time=2
log_error=/var/lib/mysql/error.log

# Binary Logging (for backups)
log_bin=/var/lib/mysql/mysql-bin
binlog_format=ROW
expire_logs_days=7
max_binlog_size=100M

[client]
default-character-set=utf8mb4
```

---

### Step 5: Create Database Initialization Script

```bash
# Create init directory
mkdir -p init

# Create initialization script
nano init/01-create-databases.sql
```

Add this SQL script:

```sql
-- Create databases for Laravel applications
CREATE DATABASE IF NOT EXISTS laravel_app1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS laravel_app2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create dedicated users for each database
CREATE USER IF NOT EXISTS 'laravel_user1'@'172.%.%.%' IDENTIFIED BY 'CHANGE_USER1_PASSWORD';
CREATE USER IF NOT EXISTS 'laravel_user2'@'172.%.%.%' IDENTIFIED BY 'CHANGE_USER2_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON laravel_app1.* TO 'laravel_user1'@'172.%.%.%';
GRANT ALL PRIVILEGES ON laravel_app2.* TO 'laravel_user2'@'172.%.%.%';

-- Flush privileges
FLUSH PRIVILEGES;
```

Generate passwords for database users:

```bash
# Generate password for laravel_user1
openssl rand -base64 24

# Generate password for laravel_user2
openssl rand -base64 24
```

Update the passwords in the SQL script.

---

### Step 6: Create Required Directories

```bash
# Create directories
mkdir -p data backups

# Set permissions
chmod -R 700 data
chmod -R 755 backups
```

---

### Step 7: Deploy MySQL Container

```bash
# Start MySQL
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

Wait for MySQL to initialize (first start takes longer).

---

### Step 8: Verify MySQL Installation

```bash
# Connect to MySQL
docker exec -it mysql-server mysql -u root -p

# Enter root password when prompted
```

Run these commands in MySQL:

```sql
-- Show databases
SHOW DATABASES;

-- Show users
SELECT user, host FROM mysql.user;

-- Test database access
USE laravel_app1;
SHOW TABLES;

-- Exit
EXIT;
```

---

## Part B: PostgreSQL Setup for Telegram Bot

### Step 1: Create PostgreSQL Directory

```bash
# Create PostgreSQL directory
mkdir -p ~/docker/postgresql

# Navigate to directory
cd ~/docker/postgresql
```

---

### Step 2: Create PostgreSQL Docker Compose File

```bash
nano docker-compose.yml
```

Add this configuration:

```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:16-alpine
    container_name: postgresql-server
    restart: unless-stopped
    environment:
      POSTGRES_USER: "postgres"
      POSTGRES_PASSWORD: "CHANGE_POSTGRES_PASSWORD"
      POSTGRES_DB: "postgres"
      PGDATA: "/var/lib/postgresql/data/pgdata"
      TZ: "Asia/Makassar"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d
      - ./backups:/backups
    networks:
      - db-network
    ports:
      # Only expose internally, not to host
      # - "5432:5432"  # Commented out for security
    command:
      - "postgres"
      - "-c"
      - "max_connections=100"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "maintenance_work_mem=64MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "work_mem=2621kB"
      - "-c"
      - "min_wal_size=1GB"
      - "-c"
      - "max_wal_size=4GB"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
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
```

---

### Step 3: Generate PostgreSQL Password

```bash
# Generate secure password
openssl rand -base64 32
```

Update the password in docker-compose.yml and save it securely.

---

### Step 4: Create PostgreSQL Initialization Script

```bash
# Create init directory
mkdir -p init

# Create initialization script
nano init/01-create-telegram-db.sql
```

Add this SQL script:

```sql
-- Create database for Telegram bot
CREATE DATABASE telegram_bot;

-- Create dedicated user
CREATE USER telegram_user WITH ENCRYPTED PASSWORD 'CHANGE_TELEGRAM_USER_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE telegram_bot TO telegram_user;

-- Connect to telegram_bot database
\c telegram_bot

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO telegram_user;
```

Generate password:

```bash
# Generate password for telegram_user
openssl rand -base64 24
```

Update the password in the SQL script.

---

### Step 5: Create Required Directories

```bash
# Create directories
mkdir -p data backups

# Set permissions
chmod -R 700 data
chmod -R 755 backups
```

---

### Step 6: Deploy PostgreSQL Container

```bash
# Start PostgreSQL
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

---

### Step 7: Verify PostgreSQL Installation

```bash
# Connect to PostgreSQL
docker exec -it postgresql-server psql -U postgres

# Run these commands in psql:
```

```sql
-- List databases
\l

-- List users
\du

-- Connect to telegram_bot database
\c telegram_bot

-- List tables (should be empty initially)
\dt

-- Exit
\q
```

---

## Part C: Database Security Best Practices

### MySQL Security Checklist

```bash
# Connect to MySQL
docker exec -it mysql-server mysql -u root -p
```

Run these security commands:

```sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove test database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- Ensure root can only connect from specific hosts
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1', '172.%.%.%');

-- Flush privileges
FLUSH PRIVILEGES;

-- Exit
EXIT;
```

---

### PostgreSQL Security Configuration

Create additional security config:

```bash
cd ~/docker/postgresql

# Create custom postgresql.conf
nano postgresql.conf
```

Add these security settings:

```ini
# Connection Settings
listen_addresses = '*'
max_connections = 100

# Security Settings
ssl = off
password_encryption = scram-sha-256

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_statement = 'mod'
log_connections = on
log_disconnections = on
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Performance
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
```

---

## Part D: Database Backup Scripts

### MySQL Backup Script

```bash
nano ~/scripts/backup-mysql.sh
```

Add this content:

```bash
#!/bin/bash
# MySQL backup script

BACKUP_DIR="$HOME/docker/mysql/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER="mysql-server"
MYSQL_ROOT_PASSWORD="YOUR_ROOT_PASSWORD"

mkdir -p "$BACKUP_DIR"

echo "Starting MySQL backup..."

# Backup all databases
docker exec "$CONTAINER" mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" \
  --all-databases \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --routines \
  --triggers \
  --events \
  | gzip > "$BACKUP_DIR/mysql-all-databases_$DATE.sql.gz"

# Backup individual databases
for DB in laravel_app1 laravel_app2; do
  echo "Backing up database: $DB"
  docker exec "$CONTAINER" mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" \
    --single-transaction \
    --quick \
    --lock-tables=false \
    --routines \
    --triggers \
    "$DB" | gzip > "$BACKUP_DIR/mysql-${DB}_$DATE.sql.gz"
done

echo "MySQL backup complete!"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "mysql-*.sql.gz" -mtime +7 -delete

# Show backup size
du -sh "$BACKUP_DIR"
```

Make executable:

```bash
chmod +x ~/scripts/backup-mysql.sh
```

---

### PostgreSQL Backup Script

```bash
nano ~/scripts/backup-postgresql.sh
```

Add this content:

```bash
#!/bin/bash
# PostgreSQL backup script

BACKUP_DIR="$HOME/docker/postgresql/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER="postgresql-server"

mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup..."

# Backup all databases
docker exec "$CONTAINER" pg_dumpall -U postgres \
  | gzip > "$BACKUP_DIR/postgresql-all-databases_$DATE.sql.gz"

# Backup telegram_bot database
echo "Backing up telegram_bot database..."
docker exec "$CONTAINER" pg_dump -U postgres telegram_bot \
  | gzip > "$BACKUP_DIR/postgresql-telegram_bot_$DATE.sql.gz"

echo "PostgreSQL backup complete!"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "postgresql-*.sql.gz" -mtime +7 -delete

# Show backup size
du -sh "$BACKUP_DIR"
```

Make executable:

```bash
chmod +x ~/scripts/backup-postgresql.sh
```

---

### Schedule Automated Backups

```bash
# Edit crontab
crontab -e
```

Add these lines:

```
# MySQL backup daily at 3 AM
0 3 * * * /home/deploy/scripts/backup-mysql.sh >> /home/deploy/logs/mysql-backup.log 2>&1

# PostgreSQL backup daily at 3:30 AM
30 3 * * * /home/deploy/scripts/backup-postgresql.sh >> /home/deploy/logs/postgresql-backup.log 2>&1
```

---

## Part E: Database Monitoring

### Create Database Monitoring Script

```bash
nano ~/scripts/monitor-databases.sh
```

Add this content:

```bash
#!/bin/bash
# Database monitoring script

echo "=== MySQL Status ==="
docker exec mysql-server mysqladmin -u root -p"YOUR_ROOT_PASSWORD" status
echo ""

echo "=== MySQL Processes ==="
docker exec mysql-server mysqladmin -u root -p"YOUR_ROOT_PASSWORD" processlist
echo ""

echo "=== PostgreSQL Status ==="
docker exec postgresql-server pg_isready -U postgres
echo ""

echo "=== PostgreSQL Connections ==="
docker exec postgresql-server psql -U postgres -c "SELECT count(*) as connections FROM pg_stat_activity;"
echo ""

echo "=== Database Container Stats ==="
docker stats --no-stream mysql-server postgresql-server
```

Make executable:

```bash
chmod +x ~/scripts/monitor-databases.sh
```

---

## Verification Checklist

### MySQL
- [x] MySQL container running
- [x] Root password set and secured
- [x] Database users created with limited privileges
- [x] Databases created and accessible
- [x] Custom configuration applied
- [x] Backup script created and tested
- [x] Automated backups scheduled

### PostgreSQL
- [x] PostgreSQL container running
- [x] Postgres password set and secured
- [x] Database user created with limited privileges
- [x] telegram_bot database created
- [x] Backup script created and tested
- [x] Automated backups scheduled

---

## Connection Strings for Applications

### MySQL Connection (Laravel .env)

```env
DB_CONNECTION=mysql
DB_HOST=mysql-server
DB_PORT=3306
DB_DATABASE=laravel_app1
DB_USERNAME=laravel_user1
DB_PASSWORD=your_generated_password
```

### PostgreSQL Connection (Python)

```python
# Using psycopg2
DATABASE_URL = "postgresql://telegram_user:your_generated_password@postgresql-server:5432/telegram_bot"

# Or using SQLAlchemy
SQLALCHEMY_DATABASE_URI = "postgresql://telegram_user:your_generated_password@postgresql-server:5432/telegram_bot"
```

---

## Troubleshooting

### MySQL Connection Issues

```bash
# Check container logs
docker logs mysql-server

# Test connection
docker exec -it mysql-server mysql -u root -p

# Check network
docker network inspect db-network
```

### PostgreSQL Connection Issues

```bash
# Check container logs
docker logs postgresql-server

# Test connection
docker exec -it postgresql-server psql -U postgres

# Check if ready
docker exec postgresql-server pg_isready -U postgres
```

### Restore from Backup

**MySQL**:
```bash
# Restore specific database
gunzip < backup.sql.gz | docker exec -i mysql-server mysql -u root -p"PASSWORD" database_name
```

**PostgreSQL**:
```bash
# Restore specific database
gunzip < backup.sql.gz | docker exec -i postgresql-server psql -U postgres telegram_bot
```

---

## Next Steps

Proceed to [`06-APPLICATION-ENVIRONMENTS.md`](06-APPLICATION-ENVIRONMENTS.md) to set up Laravel, Python, and Spring Kotlin environments.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-07  
**Tested On**: Ubuntu 24.04 LTS with MySQL 8.0 and PostgreSQL 16
