"""
Configuration management for Telegram Binance Bot.

This module handles loading and validating configuration from environment variables.
"""

import os
from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    # Telegram Configuration
    bot_token: str
    telegram_group_id: str
    binance_api_key: str
    admin_user_id: Optional[int] = None

    # Bot Behavior Configuration
    log_level: str = "INFO"
    max_post_length: int = 1000
    rate_limit: int = 60
    enable_scheduled_posts: bool = True
    enable_auto_replies: bool = True

    # Content Configuration
    allowed_hashtags: str = "#crypto,#btc,#eth,#trading,#binance,#square"
    default_post_type: str = "text"

    # Performance Configuration
    max_memory_usage: int = 512
    max_concurrent_requests: int = 10

    # Security Configuration
    enable_csrf_protection: bool = True
    secret_key: str = "your_secret_key_here"

    # Additional Settings
    environment: str = "production"
    debug: bool = False
    log_file: str = "bot.log"
    max_log_size: int = 10485760  # 10MB
    backup_log_count: int = 5

    @property
    def allowed_hashtags_list(self) -> List[str]:
        """Return allowed hashtags as a list."""
        return [tag.strip() for tag in self.allowed_hashtags.split(",") if tag.strip()]

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            Config instance with loaded values
        """
        # Load .env file if provided
        if env_file and os.path.exists(env_file):
            cls._load_env_file(env_file)
        elif os.path.exists(".env"):
            cls._load_env_file(".env")

        # Load from environment variables
        bot_token = os.getenv("BOT_TOKEN", "")
        telegram_group_id = os.getenv("TELEGRAM_GROUP_ID", "")
        binance_api_key = os.getenv("BINANCE_API_KEY", "")

        # Validate required fields
        if not bot_token:
            raise ValueError("BOT_TOKEN is required but not set")
        if not telegram_group_id:
            raise ValueError("TELEGRAM_GROUP_ID is required but not set")
        if not binance_api_key:
            raise ValueError("BINANCE_API_KEY is required but not set")

        admin_user_id_str = os.getenv("ADMIN_USER_ID", "")
        admin_user_id = int(admin_user_id_str) if admin_user_id_str else None

        return cls(
            bot_token=bot_token,
            telegram_group_id=telegram_group_id,
            binance_api_key=binance_api_key,
            admin_user_id=admin_user_id,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_post_length=int(os.getenv("MAX_POST_LENGTH", "1000")),
            rate_limit=int(os.getenv("RATE_LIMIT", "60")),
            enable_scheduled_posts=os.getenv("ENABLE_SCHEDULED_POSTS", "true").lower() == "true",
            enable_auto_replies=os.getenv("ENABLE_AUTO_REPLIES", "true").lower() == "true",
            allowed_hashtags=os.getenv("ALLOWED_HASHTAGS", "#crypto,#btc,#eth,#trading,#binance,#square"),
            default_post_type=os.getenv("DEFAULT_POST_TYPE", "text"),
            max_memory_usage=int(os.getenv("MAX_MEMORY_USAGE", "512")),
            max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            enable_csrf_protection=os.getenv("ENABLE_CSRF_PROTECTION", "true").lower() == "true",
            secret_key=os.getenv("SECRET_KEY", "your_secret_key_here"),
            environment=os.getenv("ENVIRONMENT", "production"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_file=os.getenv("LOG_FILE", "bot.log"),
            max_log_size=int(os.getenv("MAX_LOG_SIZE", "10485760")),
            backup_log_count=int(os.getenv("BACKUP_LOG_COUNT", "5")),
        )

    @staticmethod
    def _load_env_file(env_file: str) -> None:
        """Load environment variables from a .env file."""
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.

        Returns:
            List of validation messages (empty if all valid)
        """
        warnings = []

        if self.environment == "production" and self.debug:
            warnings.append("DEBUG is enabled in production environment")

        if self.max_post_length > 4096:
            warnings.append("MAX_POST_LENGTH exceeds Telegram's limit of 4096 characters")

        if self.rate_limit < 1:
            warnings.append("RATE_LIMIT should be at least 1")

        if self.max_concurrent_requests < 1:
            warnings.append("MAX_CONCURRENT_REQUESTS should be at least 1")

        if not self.allowed_hashtags_list:
            warnings.append("ALLOWED_HASHTAGS is empty")

        if self.secret_key == "your_secret_key_here":
            warnings.append("SECRET_KEY is using default value - change it in production")

        return warnings


def get_config() -> Config:
    """Get configuration instance (loads from .env if exists)."""
    return Config.load_from_env()