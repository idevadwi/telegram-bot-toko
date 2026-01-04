# Telegram Bot Toko - Product Price Lookup System

An automated system that extracts product data from a IPOS 5 (Point of Sale) system and makes it searchable via Telegram bot.

## 📋 Overview

This project provides a Telegram bot interface for querying product prices from a retail store's inventory system. It automatically synchronizes data from Dropbox backups of an IPOS database and makes it accessible through a simple Telegram interface.

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Dropbox API   │────▶│  DropboxDownloader│────▶│  Docker PostgreSQL│────▶│  DatabaseExtractor│
│   (.i5bu files) │     │  (Python module)  │     │    (Database)     │     │  (Python module)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                       │
                                                                                       ▼
                                                                              ┌─────────────────┐
                                                                              │  CSV Exporter   │
                                                                              │  (Python)       │
                                                                              └─────────────────┘
                                                                                       │
                                                                                       ▼
                                                                              ┌─────────────────┐
                                                                              │  Telegram Bot   │
                                                                              │  (bot.py)       │
                                                                              └─────────────────┘
                                                                                       │
                                                                                       ▼
                                                                              ┌─────────────────┐
                                                                              │   Users/Staff   │
                                                                              │  (Search Prices)│
                                                                              └─────────────────┘
```

## 📁 Project Structure

```
telegram-bot-toko/
├── config/                    # Configuration files
│   ├── .env                 # Environment variables (gitignored)
│   └── .env.example         # Template
├── src/                       # Source code
│   ├── core/                # Core modules
│   │   ├── config.py         # Configuration management
│   │   ├── logger.py         # Logging setup
│   │   └── exceptions.py     # Custom exceptions
│   ├── data/                # Data processing
│   │   ├── models.py         # Data models
│   │   ├── validator.py      # Data validation
│   │   ├── downloader.py     # Dropbox integration
│   │   └── extractor.py      # Database operations
│   ├── bot/                 # Telegram bot
│   │   └── bot.py          # Bot application
│   ├── database/            # Database modules
│   └── utils/               # Utilities
├── scripts/                   # Utility scripts
│   ├── sync.py             # Main sync orchestration
│   ├── health_check.sh     # Health monitoring
│   ├── backup.sh          # Manual backup
│   ├── monitor.sh         # System monitoring
│   └── backup_config.sh   # Configuration backup
├── docker/                    # Docker configuration
│   ├── Dockerfile          # Bot container
│   └── docker-compose.yml  # Service orchestration
├── tests/                     # Test suite
│   ├── test_downloader.py
│   ├── test_validator.py
│   └── conftest.py
├── data/                      # Data storage
│   ├── backups/            # .i5bu backup files
│   └── exports/            # CSV exports
├── logs/                      # Application logs
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md      # Architecture design
│   ├── COMPONENTS.md        # Component diagrams
│   ├── MIGRATION.md         # Migration plan
│   ├── RECOMMENDATIONS.md   # Recommendations
│   ├── MIGRATION_COMPLETE.md # Migration status
│   └── DEPLOYMENT.md        # VPS deployment guide
├── Makefile                  # Common commands
├── requirements.txt           # Python dependencies
└── .gitignore              # Git ignore rules
```

## 🚀 Features

- **Automated Data Sync**: Downloads latest database backups from Dropbox using Python API client
- **Product Search**: Search products by name via Telegram
- **Price Information**: Displays both cost price (harga pokok) and selling price (harga jual)
- **Real-time Updates**: Reload CSV data on-demand via `/reload` command
- **Version Tracking**: Check data timestamp with `/version` command
- **Indonesian Language**: Full Indonesian language interface
- **Automatic Cleanup**: Keeps only the 5 most recent CSV files
- **Health Monitoring**: System health checks via [`scripts/health_check.sh`](scripts/health_check.sh)
- **Manual Backups**: Backup configuration and data via [`scripts/backup.sh`](scripts/backup.sh)
- **Docker Support**: Containerized PostgreSQL database
- **Comprehensive Logging**: Structured logging with color-coded output
- **Error Handling**: Robust error handling with custom exceptions
- **Testing**: Unit test infrastructure with pytest

## 📦 Prerequisites

### System Requirements
- **Operating System**: Linux/Unix (tested on Linux)
- **Docker**: For running PostgreSQL container
- **Docker Compose**: For managing database containers
- **Python 3.8+**: For running the Telegram bot
- **Bash**: For running shell scripts

### Required Software
- Docker & Docker Compose
- Python 3.8 or higher
- pip (Python package manager)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd telegram-bot-toko
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or use Make:

```bash
make install
```

### 3. Configure Environment Variables

Copy the example environment file and update it with your credentials:

```bash
cp config/.env.example config/.env
```

Edit [`config/.env`](config/.env) with your settings:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_ADMIN_CHAT_ID=your_admin_chat_id_here

# Dropbox Configuration
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
DROPBOX_REFRESH_TOKEN=your_dropbox_refresh_token
DROPBOX_FOLDER_PATH=/IPOS

# Database Configuration
DB_NAME=i5bu
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Path Configuration
PROJECT_ROOT=/path/to/telegram-bot-toko
DATA_DIR=/path/to/telegram-bot-toko/data
BACKUPS_DIR=/path/to/telegram-bot-toko/data/backups
EXPORTS_DIR=/path/to/telegram-bot-toko/data/exports
LOGS_DIR=/path/to/telegram-bot-toko/logs

# Application Configuration
MAX_CSV_FILES=5
LOG_LEVEL=INFO
```

### 4. Start PostgreSQL Container

```bash
make docker-up
```

Or manually:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 5. Verify Installation

Run the health check script:

```bash
./scripts/health_check.sh
```

## 🎯 Usage

### Quick Start (All-in-One Sync)

Run the complete sync process (download, restore, export):

```bash
python scripts/sync.py
```

Or use Make:

```bash
make sync
```

This will:
1. Download the latest backup from Dropbox
2. Validate the backup file
3. Restore the PostgreSQL database
4. Export product data to CSV
5. Validate the CSV file
6. Clean up old files (keeping only the 5 most recent)

### Start the Telegram Bot

Run the bot in the foreground:

```bash
make run
```

Or manually:

```bash
python -m src.bot.bot
```

Run the bot in the background:

```bash
make bot
```

### Manual Backup

Create a manual backup of configuration and data:

```bash
./scripts/backup.sh
```

This will create a timestamped backup in `backups/manual/`.

### System Monitoring

Run comprehensive system monitoring:

```bash
./scripts/monitor.sh
```

Or use Make:

```bash
make monitor
```

This will display:
- Disk usage
- Memory usage
- PostgreSQL container status
- Bot status
- Latest CSV file age
- Latest backup information
- Recent sync logs

### Configuration Backup

Backup configuration files:

```bash
./scripts/backup_config.sh
```

Or use Make:

```bash
make backup-config
```

This creates a timestamped backup of critical configuration files in `backups/config/`.

## 🤖 Telegram Bot Commands

### `/start`
Displays welcome message and usage instructions.

**Example:**
```
👋 Selamat datang!
Ketik nama barang untuk mencari harga.

Perintah tambahan:
/reload - Muat ulang file CSV
/version - Versi data saat ini

Contoh:
🔍 BERAS → Menampilkan semua jenis beras.
🔍 SABUN → Menampilkan semua produk sabun.
```

### `/reload`
Reloads the latest CSV file from the exports directory.

**Example:**
```
✅ File CSV dimuat ulang dari:
`/path/to/telegram-bot-toko/data/exports/28122025-1905.csv`
```

### `/version`
Shows the timestamp of the currently loaded CSV data.

**Example:**
```
📦 Versi data saat ini:
`2025-12-28 19:05:00`
```

### Product Search
Simply type a product name to search for it.

**Example:**
```
User: BERAS

Bot: 📦 *Hasil Pencarian:*
🔹 *BERAS PREMIUM*
   📦 Konversi: 1
   📏 Satuan: KG
   💰 Harga Pokok: Rp12,000
   🛒 Harga Jual: Rp15,000

🔹 *BERAS MERAH*
   📦 Konversi: 1
   📏 Satuan: KG
   💰 Harga Pokok: Rp14,000
   🛒 Harga Jual: Rp18,000
```

## 📊 Data Schema

The CSV files contain the following product information:

| Column | Description | Example |
|--------|-------------|---------|
| `namaitem` | Product name | "BERAS PREMIUM" |
| `konversi` | Conversion factor | 1 |
| `satuan` | Unit of measurement | "KG" |
| `hargapokok` | Cost price (IDR) | 12000 |
| `hargajual` | Selling price (IDR) | 15000 |

## 🔁 Automation

### Setting Up Cron Jobs

For automated daily updates, you can set up cron jobs:

```bash
# Edit crontab
crontab -e
```

Add the following entries:

```bash
# Sync at 10:00 AM daily
0 10 * * * cd /path/to/telegram-bot-toko && python scripts/sync.py >> logs/sync_10am.log 2>&1

# Sync at 7:00 PM daily
0 19 * * * cd /path/to/telegram-bot-toko && python scripts/sync.py >> logs/sync_7pm.log 2>&1

# Health check every hour
0 * * * * cd /path/to/telegram-bot-toko && ./scripts/health_check.sh >> logs/health.log 2>&1

# Manual backup daily at 11:00 PM
0 23 * * * cd /path/to/telegram-bot-toko && ./scripts/backup.sh >> logs/backup.log 2>&1
```

For detailed VPS deployment instructions, see:
- **Quick Start**: [`docs/DEPLOYMENT_QUICKSTART.md`](docs/DEPLOYMENT_QUICKSTART.md) - 20-minute deployment guide
- **Full Guide**: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - Comprehensive deployment documentation

## 🧪 Testing

Run the test suite:

```bash
make test
```

Or manually:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## 🛠️ Troubleshooting

### Bot Not Starting

**Issue**: Bot fails to start or can't load CSV

**Solution**:
1. Ensure CSV files exist in the exports directory: `ls data/exports/`
2. Check file permissions on CSV directory
3. Verify the configuration in [`config/.env`](config/.env)
4. Check logs in `logs/` directory

### Database Restore Fails

**Issue**: Sync process fails to restore database

**Solution**:
1. Ensure Docker is running: `docker ps`
2. Check if PostgreSQL container started: `docker ps | grep pg-i5bu`
3. Verify the `.i5bu` backup file exists and is not corrupted
4. Check logs: `docker logs pg-i5bu`
5. Run health check: `./scripts/health_check.sh`

### Dropbox Download Fails

**Issue**: Sync process fails to download from Dropbox

**Solution**:
1. Verify Dropbox API credentials in [`config/.env`](config/.env)
2. Ensure refresh token is valid
3. Check network connectivity
4. Verify the Dropbox folder path exists
5. Check logs in `logs/` directory

### CSV Export Fails

**Issue**: Data export to CSV fails

**Solution**:
1. Ensure PostgreSQL container is running and ready
2. Check if the exports directory has write permissions
3. Verify the database schema matches the SQL query in [`src/data/extractor.py`](src/data/extractor.py:90)
4. Check logs for detailed error messages

## 🔐 Security Considerations

- **API Keys**: Never commit API keys or tokens to version control
- **Bot Token**: Keep your Telegram bot token secure in [`config/.env`](config/.env)
- **Dropbox Credentials**: Store refresh tokens securely in environment variables
- **File Permissions**: Set appropriate file permissions on scripts and data directories
- **Git Ignore**: Ensure `.env` is in `.gitignore`

## 📝 Development

### Project Architecture

For detailed architecture information, see:
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System architecture design
- [`docs/COMPONENTS.md`](docs/COMPONENTS.md) - Component diagrams
- [`docs/MIGRATION_COMPLETE.md`](docs/MIGRATION_COMPLETE.md) - Migration status

### Adding New Commands

To add new Telegram commands:

1. Create an async handler function in [`src/bot/bot.py`](src/bot/bot.py)
2. Register the handler using `app.add_handler(CommandHandler("command_name", handler_function))`

### Modifying Data Query

To change the SQL query for data extraction:

Edit the query in [`src/data/extractor.py`](src/data/extractor.py:90):

```python
query = """
    SELECT i.namaitem, s.jumlahkonv AS konversi, s.satuan,
           s.hargapokok, h.hargajual
    FROM tbl_item i
    JOIN tbl_itemsatuanjml s ON i.kodeitem = s.kodeitem
    JOIN tbl_itemhj h ON i.kodeitem = h.kodeitem AND s.satuan = h.satuan
"""
```

## 🐳 Docker Commands

### Build Docker Images

```bash
make docker-build
```

### Start Containers

```bash
make docker-up
```

### Stop Containers

```bash
make docker-down
```

### View Logs

```bash
make docker-logs
```

## 📄 License

This project is provided as-is for use with compatible IPOS 5 systems.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📞 Support

For issues or questions:
1. Check the documentation in [`docs/`](docs/)
2. Review logs in [`logs/`](logs/)
3. Run health check: `./scripts/health_check.sh`
4. Run tests: `pytest tests/ -v`
5. See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for VPS deployment

---

**Note**: This system is designed to work with IPOS 5 database backups (`.i5bu` format). Ensure your POS system generates compatible backup files for proper functionality.

**Version**: 2.0.0 (Python-based architecture)
**Last Updated**: 2025-01-04
