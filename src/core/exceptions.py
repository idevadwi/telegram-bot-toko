"""
Custom exceptions for the application
"""


class TelegramBotError(Exception):
    """Base exception for Telegram bot errors"""
    pass


class DropboxError(TelegramBotError):
    """Dropbox-related errors"""
    pass


class DatabaseError(TelegramBotError):
    """Database-related errors"""
    pass


class ValidationError(TelegramBotError):
    """Data validation errors"""
    pass


class ConfigurationError(TelegramBotError):
    """Configuration errors"""
    pass
