"""
Data validation module
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from core.exceptions import ValidationError
from core.logger import get_logger


class DataValidator:
    """Validates data files and structures"""

    REQUIRED_COLUMNS = ['namaitem', 'konversi', 'satuan', 'hargapokok', 'hargajual']

    def __init__(self):
        self.logger = get_logger('validator')

    def validate_backup_file(self, backup_path: Path) -> bool:
        """
        Validate that backup file exists and is not empty

        Args:
            backup_path: Path to backup file

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not backup_path.exists():
            self.logger.error(f"Backup file not found: {backup_path}")
            raise ValidationError(f"Backup file not found: {backup_path}")

        if backup_path.stat().st_size == 0:
            self.logger.error(f"Backup file is empty: {backup_path}")
            raise ValidationError(f"Backup file is empty: {backup_path}")

        self.logger.info(f"Backup file validated: {backup_path}")
        return True

    def validate_csv(self, csv_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate CSV structure and content

        Args:
            csv_path: Path to CSV file

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
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
