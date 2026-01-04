"""
Sync orchestration script
Coordinates the entire data synchronization workflow
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.config import load_config
from core.logger import setup_logging, get_logger
from core.exceptions import TelegramBotError
from data.downloader import DropboxDownloader
from data.extractor import DatabaseExtractor
from data.validator import DataValidator


def main():
    """Main sync orchestration function"""
    logger = get_logger('sync')

    try:
        # Load configuration
        config = load_config()
        setup_logging(config)
        logger.info("Starting sync process")

        # Initialize components
        downloader = DropboxDownloader(config.dropbox)
        extractor = DatabaseExtractor(config)
        validator = DataValidator()

        # Step 1: Download latest backup
        timestamp = datetime.now().strftime('%d%m%Y-%H%M')
        backup_filename = f"backup_{timestamp}.i5bu"
        backup_path = config.paths.backups_dir / backup_filename

        logger.info("Step 1: Downloading backup from Dropbox")
        downloader.download_latest(backup_path)

        # Step 2: Validate backup
        logger.info("Step 2: Validating backup file")
        if not validator.validate_backup_file(backup_path):
            raise TelegramBotError("Backup validation failed")

        # Step 3: Restore database
        logger.info("Step 3: Restoring database")
        if not extractor.ensure_database_running():
            raise TelegramBotError("Database container not running")

        if not extractor.restore_database(backup_path):
            raise TelegramBotError("Database restoration failed")

        # Step 4: Export to CSV
        logger.info("Step 4: Exporting to CSV")
        csv_filename = f"{timestamp}.csv"
        csv_path = config.paths.exports_dir / csv_filename
        extractor.export_to_csv(csv_path)

        # Step 5: Validate CSV
        logger.info("Step 5: Validating CSV")
        is_valid, error = validator.validate_csv(csv_path)
        if not is_valid:
            raise TelegramBotError(f"CSV validation failed: {error}")

        # Step 6: Cleanup old files
        logger.info("Step 6: Cleaning up old files")
        extractor.cleanup_old_files()

        logger.info("✅ Sync completed successfully")
        return 0

    except TelegramBotError as e:
        logger.error(f"❌ Sync failed: {str(e)}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
