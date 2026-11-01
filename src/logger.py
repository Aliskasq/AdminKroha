"""
Logging configuration for Telegram Binance Bot.

This module provides advanced logging functionality with different log levels,
output formats, and log rotation support.
"""

import logging
import logging.handlers
from typing import Optional, Dict, Any
import sys
from datetime import datetime
import os
import json

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Configure root logger
root_logger = logging.getLogger()
logger = logging.getLogger(__name__)


# Create console handler with debug level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create file handler with info level
log_file = "bot.log"
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to root logger
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Suppress telegram logging
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)

# Suppress HTTP library logging to reduce noise from getUpdates requests
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# Create bot-specific logger
bot_logger = logging.getLogger('telegram-binance-bot')


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Setup a logger with the given name and level.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Convert string level to logging constant
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    log_level = level_map.get(level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Only add handlers if not already added
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


class LogManager:
    """Manages logging configuration and utilities."""

    def __init__(self):
        self.log_file = "bot.log"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.datefmt = '%Y-%m-%d %H:%M:%S'

    def create_rotating_handler(self, level: str = "INFO") -> logging.handlers.RotatingFileHandler:
        """
        Create a rotating file handler.

        Args:
            level: Log level

        Returns:
            RotatingFileHandler instance
        """
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )

        log_level = getattr(logging, level.upper())
        handler.setLevel(log_level)

        formatter = logging.Formatter(self.format, self.datefmt)
        handler.setFormatter(formatter)

        return handler

    def create_console_handler(self, level: str = "INFO") -> logging.StreamHandler:
        """
        Create a console handler.

        Args:
            level: Log level

        Returns:
            StreamHandler instance
        """
        handler = logging.StreamHandler(sys.stdout)

        log_level = getattr(logging, level.upper())
        handler.setLevel(log_level)

        formatter = logging.Formatter(self.format, self.datefmt)
        handler.setFormatter(formatter)

        return handler

    def setup_module_logger(self, module_name: str, level: str = "INFO") -> logging.Logger:
        """
        Setup logger for a specific module.

        Args:
            module_name: Name of the module
            level: Log level

        Returns:
            Logger instance
        """
        logger = logging.getLogger(f"telegram-binance-bot.{module_name}")
        logger.setLevel(getattr(logging, level.upper()))

        # Add handlers if not already present
        if not logger.handlers:
            logger.addHandler(self.create_console_handler(level))
            logger.addHandler(self.create_rotating_handler(level))

        return logger

    def log_bot_start(self):
        """Log bot start information."""
        logger.info("=" * 50)
        logger.info("Telegram Binance Bot Starting")
        logger.info(f"Version: 1.0.0")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info("=" * 50)

    def log_bot_shutdown(self):
        """Log bot shutdown information."""
        logger.info("=" * 50)
        logger.info("Telegram Binance Bot Shutting Down")
        logger.info(f"Shutdown at: {datetime.now().isoformat()}")
        logger.info("=" * 50)

    def log_api_call(
        self,
        service: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        user_id: Optional[int] = None
    ):
        """
        Log API call information.

        Args:
            service: Service name
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            duration: Request duration in seconds
            user_id: User ID (optional)
        """
        user_info = f" (User: {user_id})" if user_id else ""

        log_message = (
            f"API Call: {service} {method} {endpoint} "
            f"Status: {status_code} "
            f"Duration: {duration:.3f}s{user_info}"
        )

        if status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def log_error_with_context(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        user_id: Optional[int] = None
    ):
        """
        Log error with additional context.

        Args:
            error: Exception
            context: Additional context information
            user_id: User ID (optional)
        """
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user_id,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        logger.error(f"Error occurred: {json.dumps(error_info, indent=2)}")

    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Statistics dictionary
        """
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()

            stats = {
                'total_lines': len(lines),
                'error_count': len([line for line in lines if 'ERROR' in line]),
                'warning_count': len([line for line in lines if 'WARNING' in line]),
                'info_count': len([line for line in lines if 'INFO' in line]),
                'debug_count': len([line for line in lines if 'DEBUG' in line]),
                'last_line': lines[-1].strip() if lines else None,
                'log_file_size': os.path.getsize(self.log_file) if os.path.exists(self.log_file) else 0
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get log stats: {e}")
            return {'error': str(e)}
