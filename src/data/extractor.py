"""
Database extractor module
"""
import subprocess
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..core.config import AppConfig
from ..core.exceptions import DatabaseError
from ..core.logger import get_logger


class DatabaseExtractor:
    """Handles database restoration and CSV export"""

    def __init__(self, config: AppConfig):
        """
        Initialize database extractor

        Args:
            config: Application configuration object
        """
        self.config = config
        self.logger = get_logger('extractor')

    def ensure_database_running(self) -> bool:
        """
        Ensure PostgreSQL container is running

        Returns:
            bool: True if database is running
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                check=True
            )
            return 'pg-i5bu' in result.stdout
        except subprocess.CalledProcessError:
            return False

    def restore_database(self, backup_file: Path) -> bool:
        """
        Restore database from backup file

        Args:
            backup_file: Path to backup file

        Returns:
            bool: True if restoration successful

        Raises:
            DatabaseError: If restoration fails
        """
        self.logger.info(f"Restoring database from: {backup_file}")

        commands = [
            f"docker exec -u postgres pg-i5bu dropdb --if-exists {self.config.database.database}",
            f"docker exec -u postgres pg-i5bu createdb {self.config.database.database}",
            f"docker exec -u postgres pg-i5bu pg_restore -U postgres "
            f"--no-owner --no-privileges -d {self.config.database.database} /backup/{backup_file.name}"
        ]

        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Command failed: {cmd}")
                self.logger.error(result.stderr)
                raise DatabaseError(f"Database restoration failed: {result.stderr}")

        self.logger.info("Database restored successfully")
        return True

    def export_to_csv(self, output_path: Path) -> Path:
        """
        Export product data to CSV

        Args:
            output_path: Path where CSV will be saved

        Returns:
            Path: Path to exported CSV file

        Raises:
            DatabaseError: If export fails
        """
        query = """
            SELECT i.namaitem, s.jumlahkonv AS konversi, s.satuan,
                   s.hargapokok, h.hargajual
            FROM tbl_item i
            JOIN tbl_itemsatuanjml s ON i.kodeitem = s.kodeitem
            JOIN tbl_itemhj h ON i.kodeitem = h.kodeitem AND s.satuan = h.satuan
        """

        cmd = (
            f"docker exec -u postgres pg-i5bu psql -U postgres "
            f"-d {self.config.database.database} -c "
            f"\"\\COPY ({query}) TO '/output/{output_path.name}' WITH CSV HEADER\""
        )

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.logger.error("CSV export failed")
            self.logger.error(result.stderr)
            raise DatabaseError(f"CSV export failed: {result.stderr}")

        self.logger.info(f"Exported to: {output_path}")
        return output_path

    def load_csv(self, csv_path: Path) -> pd.DataFrame:
        """
        Load CSV file into DataFrame

        Args:
            csv_path: Path to CSV file

        Returns:
            pd.DataFrame: Loaded data
        """
        return pd.read_csv(csv_path)

    def cleanup_old_files(self, keep_count: Optional[int] = None):
        """
        Remove old CSV files, keeping only the most recent

        Args:
            keep_count: Number of files to keep (defaults to config.max_csv_files)
        """
        keep_count = keep_count or self.config.max_csv_files

        csv_files = sorted(
            self.config.paths.exports_dir.glob('*.csv'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if len(csv_files) > keep_count:
            for old_file in csv_files[keep_count:]:
                old_file.unlink()
                self.logger.info(f"Removed old file: {old_file.name}")
