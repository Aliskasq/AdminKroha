#!/usr/bin/env python3
"""
Telegram Bot for Binance Square

Main entry point for the Telegram bot that integrates with Binance Square
API to post content, manage images, and handle cryptocurrency data.
"""

import asyncio
import signal
import sys
from typing import NoReturn

from src.bot import BinanceSquareBot
from src.config import Config
from src.logger import LogManager


def main() -> NoReturn:
    """
    Main entry point for the bot.

    This function initializes the bot, sets up signal handlers, and starts the bot.
    """
    # Setup logging
    log_manager = LogManager()
    log_manager.log_bot_start()

    try:
        # Load configuration
        config = Config.load_from_env()

        # Create and start bot
        bot = BinanceSquareBot(config)

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            log_manager.log_bot_shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the bot
        bot.run()

    except Exception as e:
        print(f"Error starting bot: {e}")
        log_manager.log_bot_shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()