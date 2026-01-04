"""
Data models for the application
"""
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
