"""
Database extractor module
"""
import os
import subprocess
import pandas as pd
import psycopg2
from pathlib import Path
from typing import Optional
from datetime import datetime
from core.config import AppConfig
from core.exceptions import DatabaseError
from core.logger import get_logger


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
        Ensure PostgreSQL database is accessible

        Returns:
            bool: True if database is running and accessible
        """
        try:
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.database,
                user=self.config.database.user,
                password=self.config.database.password,
                connect_timeout=5
            )
            conn.close()
            self.logger.info("Database connection successful")
            return True
        except psycopg2.OperationalError as e:
            self.logger.error(f"Database connection failed: {e}")
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

        # Build PostgreSQL connection string and parameters
        pg_conn = (
            f"postgresql://{self.config.database.user}:{self.config.database.password}"
            f"@{self.config.database.host}:{self.config.database.port}"
            f"/{self.config.database.database}"
        )

        # Connection parameters for pg commands
        pg_params = (
            f"-h {self.config.database.host} "
            f"-p {self.config.database.port} "
            f"-U {self.config.database.user}"
        )

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = self.config.database.password

        commands = [
            (f"dropdb {pg_params} --if-exists {self.config.database.database}", env),
            (f"createdb {pg_params} {self.config.database.database}", env),
            (f"pg_restore -d {pg_conn} "
             f"--no-owner --no-privileges --disable-triggers "
             f"{backup_file}", env)
        ]

        for cmd, cmd_env in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=cmd_env)
            # pg_restore may return non-zero exit code even with warnings
            # Check if restore actually succeeded (errors were ignored)
            if result.returncode != 0:
                if 'errors ignored on restore' in result.stderr.lower():
                    # Restore completed despite errors - this is OK
                    self.logger.warning(f"Restore completed with ignored errors: {cmd}")
                    if result.stderr:
                        self.logger.warning(result.stderr)
                else:
                    # Actual failure
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

        try:
            # Connect to database directly
            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.database,
                user=self.config.database.user,
                password=self.config.database.password
            )
            
            # Execute query and fetch results
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Write to CSV
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Exported to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error("CSV export failed")
            self.logger.error(str(e))
            raise DatabaseError(f"CSV export failed: {str(e)}")

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
