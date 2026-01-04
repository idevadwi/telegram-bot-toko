"""
Tests for Dropbox downloader module
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.data.downloader import DropboxDownloader
from src.data.models import BackupFile


@pytest.fixture
def mock_config():
    """Mock Dropbox configuration"""
    config = Mock()
    config.app_key = "test_key"
    config.app_secret = "test_secret"
    config.refresh_token = "test_token"
    config.folder_path = "/test"
    return config


@pytest.fixture
def downloader(mock_config):
    """Create downloader instance"""
    return DropboxDownloader(mock_config)


def test_refresh_access_token(downloader):
    """Test access token refresh"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {'access_token': 'new_token'}
        token = downloader.refresh_access_token()
        assert token == 'new_token'


def test_list_backups(downloader):
    """Test listing backup files"""
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'entries': [
                {
                    'name': 'backup1.i5bu',
                    'path_display': '/test/backup1.i5bu',
                    'server_modified': '2025-01-01T00:00:00Z'
                },
                {
                    'name': 'backup2.i5bu',
                    'path_display': '/test/backup2.i5bu',
                    'server_modified': '2025-01-02T00:00:00Z'
                }
            ]
        }
        backups = downloader.list_backups()
        assert len(backups) == 2
        assert isinstance(backups[0], BackupFile)
        assert backups[0].name == 'backup2.i5bu'  # Should be sorted by date, newest first
