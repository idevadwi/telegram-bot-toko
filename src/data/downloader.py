"""
Dropbox downloader module
"""
import requests
from typing import Optional
from pathlib import Path
from datetime import datetime
from .models import BackupFile
from ..core.exceptions import DropboxError
from ..core.logger import get_logger


class DropboxDownloader:
    """Handles downloading backup files from Dropbox"""

    def __init__(self, config):
        """
        Initialize Dropbox downloader

        Args:
            config: DropboxConfig object with API credentials
        """
        self.config = config
        self.logger = get_logger('downloader')
        self._access_token: Optional[str] = None

    def refresh_access_token(self) -> str:
        """
        Refresh Dropbox access token

        Returns:
            str: Fresh access token

        Raises:
            DropboxError: If token refresh fails
        """
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
        """
        List all .i5bu backup files from Dropbox

        Returns:
            list[BackupFile]: List of backup files, sorted by modification date (newest first)

        Raises:
            DropboxError: If listing fails
        """
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
        """
        Download the latest backup file from Dropbox

        Args:
            destination: Path where to save the downloaded file

        Returns:
            Path: Path to downloaded file

        Raises:
            DropboxError: If download fails
        """
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
