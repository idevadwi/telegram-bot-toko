"""
Tests for data validator module
"""
import pytest
import pandas as pd
from pathlib import Path
from src.data.validator import DataValidator
from src.core.exceptions import ValidationError


@pytest.fixture
def validator():
    """Create validator instance"""
    return DataValidator()


@pytest.fixture
def temp_csv(tmp_path):
    """Create temporary CSV file"""
    data = {
        'namaitem': ['Product 1', 'Product 2'],
        'konversi': [1, 2],
        'satuan': ['KG', 'PCS'],
        'hargapokok': [10000, 20000],
        'hargajual': [15000, 25000]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_validate_backup_file_exists(validator, tmp_path):
    """Test validation of existing backup file"""
    backup_file = tmp_path / "backup.i5bu"
    backup_file.write_text("test content")
    assert validator.validate_backup_file(backup_file) is True


def test_validate_backup_file_not_found(validator, tmp_path):
    """Test validation of non-existent backup file"""
    backup_file = tmp_path / "nonexistent.i5bu"
    with pytest.raises(ValidationError):
        validator.validate_backup_file(backup_file)


def test_validate_backup_file_empty(validator, tmp_path):
    """Test validation of empty backup file"""
    backup_file = tmp_path / "empty.i5bu"
    backup_file.write_text("")
    with pytest.raises(ValidationError):
        validator.validate_backup_file(backup_file)


def test_validate_csv_success(validator, temp_csv):
    """Test successful CSV validation"""
    is_valid, error = validator.validate_csv(temp_csv)
    assert is_valid is True
    assert error is None


def test_validate_csv_missing_columns(validator, tmp_path):
    """Test CSV validation with missing columns"""
    data = {'namaitem': ['Product 1']}
    df = pd.DataFrame(data)
    csv_path = tmp_path / "invalid.csv"
    df.to_csv(csv_path, index=False)

    is_valid, error = validator.validate_csv(csv_path)
    assert is_valid is False
    assert "Missing columns" in error


def test_validate_csv_empty(validator, tmp_path):
    """Test validation of empty CSV"""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("namaitem,konversi,satuan,hargapokok,hargajual\n")

    is_valid, error = validator.validate_csv(csv_path)
    assert is_valid is False
    assert "empty" in error
