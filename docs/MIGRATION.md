# Migration Plan - Telegram Bot Toko

## Overview

This document provides a detailed plan for migrating the current project structure to the improved architecture outlined in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Pre-Migration Checklist

### Backup Current State

```bash
# Create backup of current working directory
cd ..
cp -r telegram-bot-toko telegram-bot-toko-backup-$(date +%Y%m%d)

# Export current environment variables (if any)
env | grep -E "(DROPBOX|TELEGRAM|DB_)" > backup-env.txt
```

### Verify Prerequisites

- [ ] Docker and Docker Compose installed
- [ ] Python 3.8+ installed
- [ ] pip installed
- [ ] Git initialized (if using version control)
- [ ] Backup of current working state completed
- [ ] All API credentials documented and accessible

## Phase 1: Directory Restructuring (Week 1)

### Step 1.1: Create New Directory Structure

```bash
# Create main directories
mkdir -p config src/core src/data src/bot src/database src/utils
mkdir -p scripts docker/postgres tests/fixtures
mkdir -p data/backups data/exports logs docs

# Create __init__.py files
touch src/__init__.py
touch src/core/__init__.py
touch src/data/__init__.py
touch src/bot/__init__.py
touch src/database/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py
```

### Step 1.2: Move Existing Files

```bash
# Move bot files
mv telegram-bot/bot.py src/bot/bot.py
mv telegram-bot/requirements.txt requirements.txt

# Move extraction scripts
mv i5bu-extract/extract.sh scripts/extract.sh
mv i5bu-extract/docker-compose.yml docker/docker-compose.yml

# Move backup files
mv i5bu_files/*.i5bu data/backups/

# Move exported CSV files
mv i5bu-extract/output/*.csv data/exports/

# Move download script
mv download_latest_i5bu.sh scripts/download.sh

# Remove old directories (after confirming files moved)
rm -rf telegram-bot i5bu-extract i5bu_files
```

### Step 1.3: Create Configuration Files

#### Create `.env.example`

```bash
cat > config/.env.example << 'EOF'
# Dropbox Configuration
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
DROPBOX_FOLDER_PATH=/IPOS

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USERS=123456789,987654321

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=postgres

# Application Configuration
MAX_CSV_FILES=5
SEARCH_RESULTS_LIMIT=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
EOF
```

#### Create `.env` (from existing values)

```bash
# Extract values from existing scripts
# From download_latest_i5bu.sh (if still exists)
DROPBOX_APP_KEY=$(grep "APP_KEY=" scripts/download.sh | cut -d'"' -f2)
DROPBOX_APP_SECRET=$(grep "APP_SECRET=" scripts/download.sh | cut -d'"' -f2)
DROPBOX_REFRESH_TOKEN=$(grep "REFRESH_TOKEN=" scripts/download.sh | cut -d'"' -f2)

# From bot.py (if still exists)
TELEGRAM_BOT_TOKEN=$(grep 'TOKEN = "' src/bot/bot.py | cut -d'"' -f2)

# Create .env file
cat > config/.env << EOF
DROPBOX_APP_KEY=$DROPBOX_APP_KEY
DROPBOX_APP_SECRET=$DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN=$DROPBOX_REFRESH_TOKEN
DROPBOX_FOLDER_PATH=/IPOS
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ALLOWED_USERS=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=postgres
MAX_CSV_FILES=5
SEARCH_RESULTS_LIMIT=10
LOG_LEVEL=INFO
EOF
```

#### Create `.gitignore`

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
config/.env

# Data
data/backups/*.i5bu
data/exports/*.csv
!data/exports/.gitkeep

# Logs
logs/*.log

# OS
.DS_Store
Thumbs.db
EOF
```

### Step 1.4: Update Requirements

```bash
cat > requirements.txt << 'EOF'
# Core
python-dotenv==1.0.0
requests==2.31.0

# Data Processing
pandas==2.1.0

# Telegram Bot
python-telegram-bot==20.7

# Database
psycopg2-binary==2.9.9

# Logging
colorlog==6.8.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
EOF
```

## Phase 2: Core Module Implementation (Week 2)

### Step 2.1: Implement Configuration Module

Create [`src/core/config.py`](src/core/config.py):

```python
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

@dataclass
class DropboxConfig:
    app_key: str
    app_secret: str
    refresh_token: str
    folder_path: str

@dataclass
class TelegramConfig:
    bot_token: str
    allowed_users: list[int]

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

@dataclass
class PathConfig:
    project_root: Path
    data_dir: Path
    backups_dir: Path
    exports_dir: Path
    logs_dir: Path

@dataclass
class AppConfig:
    dropbox: DropboxConfig
    telegram: TelegramConfig
    database: DatabaseConfig
    paths: PathConfig
    max_csv_files: int = 5
    search_results_limit: int = 10

def load_config() -> AppConfig:
    load_dotenv('config/.env')
    project_root = Path(__file__).parent.parent.parent

    return AppConfig(
        dropbox=DropboxConfig(
            app_key=os.getenv('DROPBOX_APP_KEY'),
            app_secret=os.getenv('DROPBOX_APP_SECRET'),
            refresh_token=os.getenv('DROPBOX_REFRESH_TOKEN'),
            folder_path=os.getenv('DROPBOX_FOLDER_PATH', '/IPOS')
        ),
        telegram=TelegramConfig(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
            allowed_users=list(map(int, filter(None, os.getenv('ALLOWED_USERS', '').split(','))))
        ),
        database=DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'i5bu'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        ),
        paths=PathConfig(
            project_root=project_root,
            data_dir=project_root / 'data',
            backups_dir=project_root / 'data' / 'backups',
            exports_dir=project_root / 'data' / 'exports',
            logs_dir=project_root / 'logs'
        ),
        max_csv_files=int(os.getenv('MAX_CSV_FILES', '5')),
        search_results_limit=int(os.getenv('SEARCH_RESULTS_LIMIT', '10'))
    )
```

### Step 2.2: Implement Logging Module

Create [`src/core/logger.py`](src/core/logger.py):

```python
import logging
import sys
from pathlib import Path
from colorlog import ColoredFormatter
from .config import AppConfig

def setup_logging(config: AppConfig):
    """Setup logging configuration"""
    log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())

    # Create logs directory if it doesn't exist
    config.paths.logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for each module
    file_handler = logging.FileHandler(
        config.paths.logs_dir / 'app.log',
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)
```

### Step 2.3: Implement Custom Exceptions

Create [`src/core/exceptions.py`](src/core/exceptions.py):

```python
class TelegramBotError(Exception):
    """Base exception for Telegram bot errors"""
    pass

class DropboxError(TelegramBotError):
    """Dropbox-related errors"""
    pass

class DatabaseError(TelegramBotError):
    """Database-related errors"""
    pass

class ValidationError(TelegramBotError):
    """Data validation errors"""
    pass

class ConfigurationError(TelegramBotError):
    """Configuration errors"""
    pass
```

## Phase 3: Data Module Implementation (Week 2-3)

### Step 3.1: Implement Data Models

Create [`src/data/models.py`](src/data/models.py):

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BackupFile:
    """Represents a backup file from Dropbox"""
    name: str
    path: str
    modified: datetime

@dataclass
class ProductData:
    """Represents product data"""
    namaitem: str
    konversi: int
    satuan: str
    hargapokok: float
    hargajual: float
```

### Step 3.2: Implement Downloader Module

Create [`src/data/downloader.py`](src/data/downloader.py):

```python
import requests
from typing import Optional
from pathlib import Path
from datetime import datetime
from .models import BackupFile
from ..core.exceptions import DropboxError
from ..core.logger import get_logger

class DropboxDownloader:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger('downloader')
        self._access_token: Optional[str] = None

    def refresh_access_token(self) -> str:
        """Refresh Dropbox access token"""
        try:
            response = requests.post(
                'https://api.dropboxapi.com/oauth2/token',
                auth=(self.config.app_key, self.config.app_secret),
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.config.refresh_token
                },
                timeout=30
            )
            response.raise_for_status()
            self._access_token = response.json()['access_token']
            self.logger.debug("Access token refreshed")
            return self._access_token
        except requests.RequestException as e:
            self.logger.error(f"Failed to refresh access token: {e}")
            raise DropboxError(f"Failed to refresh access token: {e}")

    def list_backups(self) -> list[BackupFile]:
        """List all .i5bu backup files"""
        try:
            token = self.refresh_access_token()

            response = requests.post(
                'https://api.dropboxapi.com/2/files/list_folder',
                headers={'Authorization': f'Bearer {token}'},
                json={'path': self.config.folder_path},
                timeout=30
            )
            response.raise_for_status()

            files = []
            for entry in response.json().get('entries', []):
                if entry['name'].endswith('.i5bu'):
                    files.append(BackupFile(
                        name=entry['name'],
                        path=entry['path_display'],
                        modified=datetime.fromisoformat(entry['server_modified'].replace('Z', '+00:00'))
                    ))

            self.logger.info(f"Found {len(files)} backup files")
            return sorted(files, key=lambda f: f.modified, reverse=True)

        except requests.RequestException as e:
            self.logger.error(f"Failed to list backups: {e}")
            raise DropboxError(f"Failed to list backups: {e}")

    def download_latest(self, destination: Path) -> Path:
        """Download the latest backup file"""
        try:
            backups = self.list_backups()
            if not backups:
                raise DropboxError("No backup files found")

            latest = backups[0]
            self.logger.info(f"Downloading latest backup: {latest.name}")

            token = self.refresh_access_token()

            # Get temporary download link
            response = requests.post(
                'https://api.dropboxapi.com/2/files/get_temporary_link',
                headers={'Authorization': f'Bearer {token}'},
                json={'path': latest.path},
                timeout=30
            )
            response.raise_for_status()

            download_url = response.json()['link']

            # Download file
            file_response = requests.get(download_url, timeout=300)
            file_response.raise_for_status()

            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(file_response.content)

            self.logger.info(f"Downloaded to: {destination}")
            return destination

        except requests.RequestException as e:
            self.logger.error(f"Failed to download backup: {e}")
            raise DropboxError(f"Failed to download backup: {e}")
```

### Step 3.3: Implement Validator Module

Create [`src/data/validator.py`](src/data/validator.py):

```python
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from ..core.exceptions import ValidationError
from ..core.logger import get_logger

class DataValidator:
    REQUIRED_COLUMNS = ['namaitem', 'konversi', 'satuan', 'hargapokok', 'hargajual']

    def __init__(self):
        self.logger = get_logger('validator')

    def validate_backup_file(self, backup_path: Path) -> bool:
        """Validate that backup file exists and is not empty"""
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            raise ValidationError(f"Backup file not found: {backup_path}")

        if backup_path.stat().st_size == 0:
            self.logger.error(f"Backup file is empty: {backup_path}")
            raise ValidationError(f"Backup file is empty: {backup_path}")

        self.logger.info(f"Backup file validated: {backup_path}")
        return True

    def validate_csv(self, csv_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate CSV structure and content"""
        try:
            df = pd.read_csv(csv_path)

            # Check required columns
            missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                error = f"Missing columns: {missing_cols}"
                self.logger.error(error)
                return False, error

            # Check for empty data
            if df.empty:
                error = "CSV file is empty"
                self.logger.error(error)
                return False, error

            # Check for null values in critical columns
            null_counts = df[self.REQUIRED_COLUMNS].isnull().sum()
            if null_counts.any():
                error = f"Null values found: {null_counts[null_counts > 0].to_dict()}"
                self.logger.warning(error)

            self.logger.info(f"CSV validated: {csv_path} ({len(df)} rows)")
            return True, None

        except Exception as e:
            error = f"CSV validation failed: {str(e)}"
            self.logger.error(error)
            return False, error
```

## Phase 4: Bot Module Refactoring (Week 3)

### Step 4.1: Refactor Bot to Use New Modules

Update [`src/bot/bot.py`](src/bot/bot.py):

```python
import pandas as pd
import os
from glob import glob
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
)
from ..core.config import load_config
from ..core.logger import setup_logging, get_logger
from ..core.exceptions import TelegramBotError

# Load configuration
config = load_config()
setup_logging(config)
logger = get_logger('bot')

# Global Data
df = pd.DataFrame()
csv_path = ""
csv_loaded_at = None


def get_latest_csv(folder_path):
    """Get the latest CSV file from folder"""
    list_of_files = glob(os.path.join(folder_path, "*.csv"))
    if not list_of_files:
        raise TelegramBotError("❌ Tidak ada file CSV ditemukan.")
    latest_file = max(list_of_files, key=os.path.getmtime)
    return latest_file


def load_csv():
    """Load the latest CSV file"""
    global df, csv_path, csv_loaded_at
    csv_path = get_latest_csv(str(config.paths.exports_dir))
    df = pd.read_csv(csv_path)
    csv_loaded_at = datetime.fromtimestamp(os.path.getmtime(csv_path))
    logger.info(f"Reloaded CSV: {csv_path}")


def search_products(keyword):
    """Search products by keyword"""
    keyword = keyword.strip().upper()
    results = df[df["namaitem"].str.contains(keyword, case=False, na=False)].sort_values(by="namaitem")

    if results.empty:
        return "❌ Barang tidak ditemukan. Coba dengan kata lain."

    response = "📦 *Hasil Pencarian:*\n"
    count = 0
    for _, row in results.iterrows():
        response += (
            f"🔹 *{row['namaitem']}*\n"
            f"   📦 Konversi: {row['konversi']}\n"
            f"   📏 Satuan: {row['satuan']}\n"
            f"   💰 Harga Pokok: Rp{row['hargapokok']:,.0f}\n"
            f"   🛒 Harga Jual: Rp{row['hargajual']:,.0f}\n\n"
        )
        count += 1
        if count >= config.search_results_limit:
            response += "⚠️ *Terlalu banyak hasil. Gunakan kata yang lebih spesifik.*"
            break

    return response


# Telegram Handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        query = update.message.text.strip()
        response = search_products(query)
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ Terjadi kesalahan. Silakan coba lagi.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = (
        "👋 *Selamat datang!*\n"
        "Ketik *nama barang* untuk mencari harga.\n\n"
        "Perintah tambahan:\n"
        "/reload - Muat ulang file CSV\n"
        "/version - Versi data saat ini\n\n"
        "Contoh:\n"
        "🔍 *BERAS* → Menampilkan semua jenis beras.\n"
        "🔍 *SABUN* → Menampilkan semua produk sabun.\n"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def reload_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reload command"""
    try:
        load_csv()
        await update.message.reply_text(
            f"✅ File CSV dimuat ulang dari:\n`{csv_path}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error reloading CSV: {e}")
        await update.message.reply_text(f"❌ Gagal memuat ulang CSV: {e}")


async def show_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /version command"""
    if csv_loaded_at:
        await update.message.reply_text(
            f"📦 Versi data saat ini:\n`{csv_loaded_at.strftime('%Y-%m-%d %H:%M:%S')}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ CSV belum dimuat.")


def main():
    """Main function to run the bot"""
    # Load CSV at startup
    try:
        load_csv()
    except Exception as e:
        logger.error(f"Failed to load CSV at startup: {e}")

    # Initialize Bot
    app = ApplicationBuilder().token(config.telegram.bot_token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reload", reload_csv))
    app.add_handler(CommandHandler("version", show_version))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the Bot
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
```

## Phase 5: Testing (Week 3-4)

### Step 5.1: Create Test Suite

Create [`tests/test_downloader.py`](tests/test_downloader.py):

```python
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.data.downloader import DropboxDownloader
from src.data.models import BackupFile

@pytest.fixture
def mock_config():
    config = Mock()
    config.app_key = "test_key"
    config.app_secret = "test_secret"
    config.refresh_token = "test_token"
    config.folder_path = "/test"
    return config

@pytest.fixture
def downloader(mock_config):
    return DropboxDownloader(mock_config)

def test_refresh_access_token(downloader):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'access_token': 'new_token'}
        token = downloader.refresh_access_token()
        assert token == 'new_token'

def test_list_backups(downloader):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'entries': [
                {
                    'name': 'backup1.i5bu',
                    'path_display': '/test/backup1.i5bu',
                    'server_modified': '2025-01-01T00:00:00Z'
                }
            ]
        }
        backups = downloader.list_backups()
        assert len(backups) == 1
        assert isinstance(backups[0], BackupFile)
```

### Step 5.2: Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Phase 6: Deployment (Week 4)

### Step 6.1: Create Docker Configuration

Update [`docker/docker-compose.yml`](docker/docker-compose.yml):

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

networks:
  bot-network:
    driver: bridge
```

### Step 6.2: Create Dockerfile

Create [`docker/Dockerfile`](docker/Dockerfile):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p data/backups data/exports logs

# Set Python path
ENV PYTHONPATH=/app

# Run the bot
CMD ["python", "-m", "src.bot.bot"]
```

### Step 6.3: Create Makefile

Create [`Makefile`](Makefile):

```makefile
.PHONY: help install test run bot sync clean docker-build docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest tests/ -v

run: ## Run the bot
	python -m src.bot.bot

sync: ## Run sync process
	python scripts/sync.py

bot: ## Run bot in background
	nohup python -m src.bot.bot > logs/bot.log 2>&1 &

clean: ## Clean up
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker images
	docker-compose -f docker/docker-compose.yml build

docker-up: ## Start Docker containers
	docker-compose -f docker/docker-compose.yml up -d

docker-down: ## Stop Docker containers
	docker-compose -f docker/docker-compose.yml down

docker-logs: ## Show Docker logs
	docker-compose -f docker/docker-compose.yml logs -f
```

### Step 6.4: Setup Cron Jobs

```bash
# Edit crontab
crontab -e

# Add the following entries
# Sync at 10:00 AM and 7:00 PM daily
0 10 * * * cd /path/to/telegram-bot-toko && python scripts/sync.py >> logs/sync_10am.log 2>&1
0 19 * * * cd /path/to/telegram-bot-toko && python scripts/sync.py >> logs/sync_7pm.log 2>&1

# Restart bot if it crashes (every 5 minutes)
*/5 * * * * cd /path/to/telegram-bot-toko && pgrep -f "python -m src.bot.bot" > /dev/null || python -m src.bot.bot >> logs/bot.log 2>&1 &
```

## Phase 7: Monitoring & Maintenance

### Step 7.1: Setup Monitoring

Create [`scripts/health_check.sh`](scripts/health_check.sh):

```bash
#!/bin/bash

# Health check script

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
```

### Step 7.2: Create Backup Script

Create [`scripts/backup.sh`](scripts/backup.sh):

```bash
#!/bin/bash

# Backup script

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
```

## Rollback Plan

If migration fails, follow these steps:

### Step 1: Stop New System

```bash
# Stop Docker containers
docker-compose -f docker/docker-compose.yml down

# Stop bot processes
pkill -f "python -m src.bot.bot"
```

### Step 2: Restore Backup

```bash
# Navigate to backup directory
cd ../telegram-bot-toko-backup-*

# Restore original structure
cp -r . ../telegram-bot-toko/
```

### Step 3: Restart Original System

```bash
cd ../telegram-bot-toko

# Start original bot
cd telegram-bot
python bot.py
```

## Validation Checklist

After migration, verify:

- [ ] All directories created correctly
- [ ] Configuration files in place
- [ ] Environment variables loaded
- [ ] Bot starts without errors
- [ ] Bot responds to commands
- [ ] Product search works
- [ ] CSV reload works
- [ ] Sync process completes
- [ ] Database restores correctly
- [ ] CSV exports successfully
- [ ] Logs are being written
- [ ] Docker containers run
- [ ] Health check passes
- [ ] Tests pass

## Post-Migration Tasks

1. **Documentation Updates**
   - Update README with new structure
   - Update deployment guides
   - Create troubleshooting documentation

2. **Team Training**
   - Train team on new structure
   - Document common tasks
   - Create runbooks

3. **Monitoring Setup**
   - Configure log aggregation
   - Set up alerts
   - Create dashboards

4. **Performance Tuning**
   - Monitor resource usage
   - Optimize database queries
   - Tune bot performance

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | Week 1 | Directory structure, configuration files |
| Phase 2 | Week 2 | Core modules (config, logging, exceptions) |
| Phase 3 | Week 2-3 | Data modules (downloader, validator) |
| Phase 4 | Week 3 | Bot refactoring |
| Phase 5 | Week 3-4 | Test suite and testing |
| Phase 6 | Week 4 | Docker deployment |
| Phase 7 | Ongoing | Monitoring and maintenance |

## Support & Resources

- Architecture documentation: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Component diagrams: [`COMPONENTS.md`](COMPONENTS.md)
- Original README: [`README.md`](README.md)
