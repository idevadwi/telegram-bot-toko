"""
Configuration management module
"""
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass
class DropboxConfig:
    """Dropbox API configuration"""
    app_key: str
    app_secret: str
    refresh_token: str
    folder_path: str


@dataclass
class TelegramConfig:
    """Telegram Bot configuration"""
    bot_token: str
    allowed_users: list[int]


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class PathConfig:
    """Path configuration"""
    project_root: Path
    data_dir: Path
    backups_dir: Path
    exports_dir: Path
    logs_dir: Path


@dataclass
class AppConfig:
    """Main application configuration"""
    dropbox: DropboxConfig
    telegram: TelegramConfig
    database: DatabaseConfig
    paths: PathConfig
    max_csv_files: int = 5
    search_results_limit: int = 10


def load_config() -> AppConfig:
    """
    Load configuration from environment variables

    Returns:
        AppConfig: Loaded configuration object
    """
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / 'config' / '.env'
    load_dotenv(env_path)

    # Get project root directory
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
