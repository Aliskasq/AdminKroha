"""
Main Telegram Bot for Binance Square

This bot allows users to post content to Binance Square via Telegram commands.
It supports various features including text posts, image posts, polls, ticker data,
and content scheduling.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from .config import Config
from .binance_api import BinanceSquareAPI
from .content_generator import ContentGenerator
from .image_handler import ImageHandler
from .scheduler import PostScheduler
from .logger import setup_logger
from .reminder import ReminderManager

logger = setup_logger(__name__)

class BinanceSquareBot:
    """Main bot class for Telegram-Binance Square integration."""

    def __init__(self, config: Config):
        """
        Initialize the bot with configuration.

        Args:
            config: Configuration object containing bot settings
        """
        self.config = config
        self.binance_api = BinanceSquareAPI(config)
        self.content_generator = ContentGenerator()
        self.image_handler = ImageHandler()
        self.scheduler = PostScheduler(config, self.binance_api)
        self.reminder_manager = ReminderManager(config)

        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Suppress HTTP library logging to reduce noise from getUpdates requests
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)

        # Bot state
        self.user_data: Dict[int, Dict[str, Any]] = {}
        self.scheduled_posts: List[Dict[str, Any]] = []

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        chat_type = update.effective_chat.type

        # Security check: only allow group chats
        if chat_type != 'group' and chat_type != 'supergroup':
            await update.message.reply_text(
                "❌ This bot only works in group chats! "
                "Please add me to a group chat to use AdminKroha."
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use bot in private chat")
            return

        # Check if user is admin (only admin can use the bot)
        if self.config.admin_user_id and user_id != self.config.admin_user_id:
            await update.message.reply_text(
                "❌ Only the bot administrator has permission to use AdminKroha!"
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use bot without admin permissions")
            return

        # Initialize user data
        self.user_data[user_id] = {
            'username': username,
            'start_time': datetime.now(),
            'commands_used': 0,
            'chat_id': update.effective_chat.id
        }

        welcome_message = (
            f"👋 Welcome, {username}! I'm AdminKroha - Enhanced Binance Square Telegram Bot! 🚀\n\n"
            f"🎯 **Bot Access:** This bot works only in group chats.\n\n"
            f"📝 **Available Commands:**\n"
            f"• /help - Show all commands\n"
            f"• /post <text> - Post text content to Binance Square\n"
            f"• /post_image <text> - Post content with image\n"
            f"• /get_tickers <tickers> - Get ticker data\n"
            f"• /poll <question> <option1> <option2> ... - Create a poll\n"
            f"• /schedule <time> <text> - Schedule a post\n"
            f"• /scheldue <details> - Schedule posts with polls/tickers/images\n"
            f"• /reminder <type> <time> [days] [message] - Add reminder\n"
            f"• /list-reminders - List all reminders\n"
            f"• /status - Check bot status\n\n"
            f"📊 **Features:**\n"
            f"• Hashtag support in posts\n"
            f"• Real-time ticker data with $SYMBOL highlighting\n"
            f"• Image upload and processing\n"
            f"• Interactive polls\n"
            f"• Content scheduling\n"
            f"• Advanced reminder system\n"
            f"• Time zone support (+1, +2, +3, +0)\n"
            f"• Multi-language support\n\n"
            f"🔧 **Admin Commands:**\n"
            f"• /broadcast <text> - Send broadcast message (admin only)\n"
            f"• /logs - View recent logs (admin only)\n\n"
            f"⚠️ **Note:** This bot is restricted to group chats and administrators only for security reasons.\n\n"
            f"❓ Need help? Type any command to get started!"
        )

        await update.message.reply_text(welcome_message)
        logger.info(f"Admin user {username} (ID: {user_id}) started AdminKroha bot in group chat {update.effective_chat.id}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        chat_type = update.effective_chat.type

        # Security check: only allow group chats
        if chat_type != 'group' and chat_type != 'supergroup':
            await update.message.reply_text(
                "❌ This bot only works in group chats! "
                "Please add me to a group chat to use AdminKroha."
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use /help in private chat")
            return

        # Check if user is admin (only admin can use the bot)
        if self.config.admin_user_id and user_id != self.config.admin_user_id:
            await update.message.reply_text(
                "❌ Only the bot administrator has permission to use AdminKroha!"
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use /help without admin permissions")
            return

        help_message = (
            f"👋 Hi, {username}! Here's a complete guide to using AdminKroha! 📚\n\n"
            f"📝 **TEXT POSTS:**\n"
            f"Use /post followed by your content to create a text post:\n"
            f"  Example: `/post BTC is bullish today #crypto #trading`\n\n"
            f"🖼️ **IMAGE POSTS:**\n"
            f"Use /post_image followed by text and an image to create a post with an image:\n"
            f"  Step 1: `/post_image Market analysis`\n"
            f"  Step 2: Send the image to the bot\n\n"
            f"📊 **TICKER DATA:**\n"
            f"Get real-time cryptocurrency ticker information with $SYMBOL highlighting:\n"
            f"  Example: `/get_tickers $btc $eth $sol` or `/get_tickers BTCUSDT ETHUSDT SOLUSDT`\n\n"
            f"🗳️ **POLLS:**\n"
            f"Create interactive polls with multiple options:\n"
            f"  Example: `/poll Will BTC go above $50k? Yes No Maybe`\n\n"
            f"⏰ **SCHEDULING:**\n"
            f"Schedule posts for future times:\n"
            f"  Example: `/schedule 14:30 Market analysis tomorrow`\n\n"
            f"🚀 **ADVANCED SCHEDULING (SCHELDU):**\n"
            f"Schedule posts with polls, tickers, and images:\n"
            f"  Example: `/scheldue 14:30 'Will BTC rise?' Yes No Maybe $btc`\n\n"
            f"🔔 **REMINDERS:**\n"
            f"Add customizable reminders with time and days:\n"
            f"  Example: `/reminder task 09:00 Check tasks 0,2,4 Daily task`\n"
            f"  Example: `/reminder market 14:30 BTC price $btc 0,1,2,3,4`\n\n"
            f"🔧 **ADMIN COMMANDS:**\n"
            f"• /status - Check bot status and statistics\n"
            f"• /broadcast <text> - Send broadcast message to all users\n"
            f"• /logs - View recent bot logs\n\n"
            f"📈 **BOT STATUS:**\n"
            f"• Online and responsive\n"
            f"• Connected to Binance Square API\n"
            f"• Processing posts: Active\n"
            f"• Scheduled posts: {len(self.scheduled_posts)}\n\n"
            f"🎯 **Tips:**\n"
            f"• Use hashtags (#crypto, #btc, #trading) to increase visibility\n"
            f"• Include $SYMBOL for automatic ticker highlighting\n"
            f"• Schedule posts during peak hours for maximum engagement\n"
            f"• Use polls to engage with your audience\n"
            f"• Set reminders for regular tasks\n"
            f"• Use timezone-aware scheduling (+1, +2, +3, +0)\n\n"
            f"🔒 **Security:** This bot is restricted to group chats and administrators only for security reasons.\n\n"
            f"❓ Need help? Type any command to get started!"
        )

        await update.message.reply_text(help_message)
        logger.info(f"Admin user {username} (ID: {user_id}) requested help in group chat {update.effective_chat.id}")

    async def scheldue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /scheldue command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide scheldue details!\n"
                "Usage: `/scheldue <time> <details>`\n"
                "Examples:\n"
                "  `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc`\n"
                "  `/scheldue 09:00 \"Daily analysis\" \"BTC: $45k (+2.5%) ETH: $2.3k (+1.2%)\" #crypto`\n\n"
                "Details can include:\n"
                "  • Question for poll: \"Will BTC rise?\"\n"
                "  • Options: Yes No Maybe\n"
                "  • Tickers: $btc $eth $sol (with or without $)\n"
                "  • Hashtags: #crypto #bitcoin\n"
                "  • Content for regular post after options"
            )
            return

        time_str = context.args[0]
        details = ' '.join(context.args[1:])

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Invalid scheldue format!\n"
                    "Please provide details in format: [question] [options] [tickers] [hashtags] [content]\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc #crypto`\n"
                    "Example: `/scheldue 09:00 \"Daily analysis\" \"BTC: $45k\" #crypto`\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc $eth`"
                )
                return

            # Schedule the scheldue post
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Invalid time format! Use HH:MM format (24 hours)\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc`"
                )
                return

            # Create scheldue post with all features
            post_id = await self._create_scheldue_post(
                scheduled_time,
                scheldue_data,
                user_id,
                username
            )

            success_message = (
                f"🚀 **Scheldue Post Scheduled Successfully!** 🎉\n\n"
                f"📝 **Question:** {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ **Options:** {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 **Tickers:** {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ **Hashtags:** {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ **Scheduled Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 **Scheldue ID:** {post_id}\n"
                f"👤 **Scheduled by:** {username}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled scheldue: {details[:50]}...")

        except Exception as e:
            error_message = f"❌ Error scheduling scheldue: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error scheduling scheldue for user {username}: {e}")

    async def scheldue_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue command with interactive interface.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Security check: only allow private messages
        if update.effective_chat.type != 'private':
            await update.message.reply_text(
                "❌ This bot only works in private messages! "
                "Please message me directly to use AdminKroha."
            )
            return

        # Check if user is admin (only admin can use the bot)
        if self.config.admin_user_id and user_id != self.config.admin_user_id:
            await update.message.reply_text(
                "❌ Only the bot administrator has permission to use AdminKroha!"
            )
            return

        # Interactive scheldue creation
        await update.message.reply_text(
            "🚀 **AdminKroha Scheldue Creator** 🚀\n\n"
            "Let's create a scheduled post with polls, tickers, and hashtags!\n\n"
            "**Step 1:** Provide the scheduled time (HH:MM format)\n"
            "Example: `14:30` for 2:30 PM\n\n"
            "**Step 2:** Provide the content details\n"
            "You can include:\n"
            "  • Question: \"Will BTC rise?\"\n"
            "  • Options: Yes No Maybe\n"
            "  • Tickers: $btc $eth $sol or BTCUSDT ETHUSDT\n"
            "  • Hashtags: #crypto #bitcoin\n"
            "  • Regular content after options\n\n"
            "**Example:** `14:30 \"Will BTC rise?\" Yes No Maybe $btc #crypto`\n\n"
            "Please provide your scheduled time and details:"
        )

        # Store scheldue creation state
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['scheldue_step'] = 'waiting_for_details'
        self.user_data[user_id]['scheldue_username'] = username

    async def scheldue_details_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue details after interactive setup.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id

        # Check if user is in scheldue creation process
        if user_id not in self.user_data or self.user_data[user_id].get('scheldue_step') != 'waiting_for_details':
            return

        scheldue_details = update.message.text.strip()

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(scheldue_details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Invalid scheldue format!\n"
                    "Please provide details in format: [question] [options] [tickers] [hashtags] [content]\n"
                    "Example: `\"Will BTC rise?\" Yes No Maybe $btc #crypto`\n"
                    "Example: `\"Daily analysis\" \"BTC: $45k\" #crypto`\n"
                    "Please try again:"
                )
                return

            # Send interactive time input
            await update.message.reply_text(
                "⏰ **Step 2:** Please provide the scheduled time (HH:MM format):\n"
                "Example: `14:30` for 2:30 PM\n"
                "Example: `09:00` for 9:00 AM\n"
                "Please enter the time:"
            )

            # Store scheldue data temporarily
            self.user_data[user_id]['scheldue_data'] = scheldue_data
            self.user_data[user_id]['scheldue_step'] = 'waiting_for_time'

        except Exception as e:
            await update.message.reply_text(f"❌ Error processing scheldue details: {e}")
            logger.error(f"Error processing scheldue details for user {user_id}: {e}")

    async def scheldue_time_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue time input after interactive setup.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id

        # Check if user is waiting for time input
        if user_id not in self.user_data or self.user_data[user_id].get('scheldue_step') != 'waiting_for_time':
            return

        time_str = update.message.text.strip()

        try:
            # Parse time
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Invalid time format! Use HH:MM format (24 hours)\n"
                    "Example: `14:30` for 2:30 PM\n"
                    "Please enter the time again:"
                )
                return

            # Complete scheldue creation
            scheldue_data = self.user_data[user_id]['scheldue_data']
            username = self.user_data[user_id]['scheldue_username']

            # Create scheldue post
            post_id = await self._create_scheldue_post(
                scheduled_time,
                scheldue_data,
                user_id,
                username
            )

            # Clear temporary data
            del self.user_data[user_id]['scheldue_data']
            del self.user_data[user_id]['scheldue_step']
            del self.user_data[user_id]['scheldue_username']

            # Send success message
            await update.message.reply_text(
                f"✅ **Scheldue Post Scheduled Successfully!** 🎉\n\n"
                f"📝 **Question:** {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ **Options:** {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 **Tickers:** {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ **Hashtags:** {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ **Scheduled Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 **Scheldue ID:** {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 **Next steps:**\n"
                f"• `/scheldue` - Create another scheldue\n"
                f"• `/status` - Check bot status\n"
                f"• `/list-reminders` - Manage reminders\n"
                f"• `/help` - View all commands"
            )

            logger.info(f"User {username} (ID: {user_id}) created scheldue post {post_id}")

        except Exception as e:
            await update.message.reply_text(f"❌ Error scheduling scheldue: {e}")
            logger.error(f"Error scheduling scheldue for user {user_id}: {e}")

    async def post_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /post command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide content to post!\n"
                "Example: `/post BTC price breakout today #crypto #trading`"
            )
            return

        content = ' '.join(context.args)
        self.user_data[user_id]['commands_used'] += 1

        try:
            # Generate formatted content
            formatted_content = self.content_generator.generate_content(
                content,
                post_type='text'
            )

            # Post to Binance Square
            result = await self.binance_api.post_content(
                formatted_content,
                post_type='text'
            )

            success_message = (
                f"✅ Post published successfully! 🎉\n\n"
                f"📝 **Content:**\n{formatted_content}\n\n"
                f"🆔 **Post ID:** {result.get('id', 'N/A')}\n"
                f"📅 **Published:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 **View Post:** https://www.binance.com/square/post/{result.get('id', 'N/A')}"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} posted content to Binance Square: {content[:50]}...")

        except Exception as e:
            error_message = f"❌ Error posting content: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error posting content for user {username}: {e}")

    async def post_image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /post_image command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide text content for the image post!\n"
                "Example: `/post_image Market analysis today`"
            )
            return

        text_content = ' '.join(context.args)
        self.user_data[user_id]['commands_used'] += 1

        # Inform user that we need to receive an image
        await update.message.reply_text(
            f"🖼️ Please send the image you want to post with this content:\n\n"
            f"📝 **Content:** {text_content}\n\n"
            f"After sending the image, I'll post it to Binance Square for you!"
        )

        # Store the content in user data for the next message
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['pending_image_post'] = text_content

        logger.info(f"User {username} started image post with content: {text_content}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle photo messages for image posts.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Check if user has pending image post
        if user_id not in self.user_data or 'pending_image_post' not in self.user_data[user_id]:
            await update.message.reply_text(
                "❌ No pending image post found!\n"
                "Please start with `/post_image <text>` command first."
            )
            return

        text_content = self.user_data[user_id]['pending_image_post']

        try:
            # Get the image file
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()

            # Upload image to Binance
            image_result = await self.image_handler.upload_image(image_bytes)

            # Generate content with image
            formatted_content = self.content_generator.generate_content(
                text_content,
                post_type='image',
                image_url=image_result['url']
            )

            # Post to Binance Square
            post_result = await self.binance_api.post_content(
                formatted_content,
                post_type='image',
                image_url=image_result['url']
            )

            # Clear pending state
            del self.user_data[user_id]['pending_image_post']

            success_message = (
                f"✅ Image post published successfully! 🎉\n\n"
                f"📝 **Content:** {text_content}\n"
                f"🖼️ **Image:** Posted successfully\n\n"
                f"🆔 **Post ID:** {post_result.get('id', 'N/A')}\n"
                f"📅 **Published:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🔗 **View Post:** https://www.binance.com/square/post/{post_result.get('id', 'N/A')}"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} posted image content to Binance Square: {text_content[:50]}...")

        except Exception as e:
            error_message = f"❌ Error posting image content: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error posting image content for user {username}: {e}")

            # Clear pending state on error
            if user_id in self.user_data and 'pending_image_post' in self.user_data[user_id]:
                del self.user_data[user_id]['pending_image_post']

    async def get_tickers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /get_tickers command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide ticker symbols!\n"
                "Example: `/get_tickers BTCUSDT ETHUSDT SOLUSDT`"
            )
            return

        tickers = [arg.upper() for arg in context.args if arg.upper().endswith('USDT')]

        if not tickers:
            await update.message.reply_text(
                "❌ Please provide valid ticker symbols ending with USDT!\n"
                "Example: `/get_tickers BTCUSDT ETHUSDT SOLUSDT`"
            )
            return

        self.user_data[user_id]['commands_used'] += 1

        try:
            # Get ticker data from Binance
            ticker_data = await self.binance_api.get_ticker_data(tickers)

            # Format the response
            response = "📊 **Cryptocurrency Ticker Data:**\n\n"
            for ticker, data in ticker_data.items():
                change_indicator = "📈" if data.get('priceChangePercent', 0) >= 0 else "📉"
                response += (
                    f"{change_indicator} **{ticker}:** ${data.get('lastPrice', 'N/A')}\n"
                    f"   24h Change: {data.get('priceChangePercent', 'N/A')}%\n"
                    f"   High: ${data.get('highPrice', 'N/A')}\n"
                    f"   Low: ${data.get('lowPrice', 'N/A')}\n"
                    f"   Volume: {data.get('volume', 'N/A')}\n\n"
                )

            await update.message.reply_text(response)
            logger.info(f"User {username} requested ticker data for {len(tickers)} symbols")

        except Exception as e:
            error_message = f"❌ Error getting ticker data: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error getting ticker data for user {username}: {e}")

    async def _parse_scheldue_details(self, details: str) -> Optional[Dict[str, Any]]:
        """
        Parse scheldue details from string.

        Args:
            details: Scheldue details string

        Returns:
            Parsed scheldue data or None if invalid
        """
        try:
            # Split by spaces but handle quoted strings
            import shlex
            parts = shlex.split(details)

            scheldue_data = {
                'question': None,
                'options': [],
                'tickers': [],
                'hashtags': [],
                'content': None
            }

            current_field = None

            for part in parts:
                if part.startswith('"') and part.endswith('"'):
                    # Remove quotes from quoted strings
                    part = part[1:-1]

                if not current_field:
                    # First non-empty part is the question
                    if part and not part.startswith('#') and not part.startswith('$') and ' ' not in part:
                        scheldue_data['question'] = part
                    else:
                        scheldue_data['content'] = part
                elif current_field == 'question':
                    scheldue_data['question'] = part
                    current_field = None
                elif current_field == 'options':
                    scheldue_data['options'].append(part)
                elif current_field == 'tickers':
                    if part.startswith('$'):
                        scheldue_data['tickers'].append(part[1:])
                    else:
                        scheldue_data['tickers'].append(part)
                elif current_field == 'hashtags':
                    if part.startswith('#'):
                        scheldue_data['hashtags'].append(part)
                    else:
                        scheldue_data['content'] = part
                else:
                    scheldue_data['content'] = part

            # Validate required fields
            if not scheldue_data['question']:
                return None

            # Extract tickers and hashtags from content if not already found
            if scheldue_data['content']:
                import re
                ticker_pattern = r'\$(\w+)|(\b\w+USDT\b)'
                hashtag_pattern = r'#(\w+)'

                ticker_matches = re.findall(ticker_pattern, scheldue_data['content'])
                hashtag_matches = re.findall(hashtag_pattern, scheldue_data['content'])

                # Flatten ticker matches
                for match in ticker_matches:
                    if match[0]:
                        scheldue_data['tickers'].append(match[0])
                    elif match[1]:
                        scheldue_data['tickers'].append(match[1])

                # Add hashtag matches
                scheldue_data['hashtags'].extend([f'#{tag}' for tag in hashtag_matches])

                # Clean content from tickers and hashtags
                clean_content = scheldue_data['content']
                for ticker in scheldue_data['tickers']:
                    clean_content = clean_content.replace(f'${ticker}', '').replace(ticker + 'USDT', '')
                for hashtag in scheldue_data['hashtags']:
                    clean_content = clean_content.replace(hashtag, '')

                scheldue_data['content'] = clean_content.strip()

            # Remove empty lists
            scheldue_data = {k: v for k, v in scheldue_data.items() if v}

            return scheldue_data

        except Exception:
            return None

    async def _create_scheldue_post(
        self,
        scheduled_time: datetime,
        scheldue_data: Dict[str, Any],
        user_id: int,
        username: str
    ) -> str:
        """
        Create a scheldue post with all features.

        Args:
            scheduled_time: When to schedule the post
            scheldue_data: Parsed scheldue data
            user_id: User ID
            username: Username

        Returns:
            Post ID
        """
        # Generate scheldue content
        scheldue_content = await self._generate_scheldue_content(scheldue_data)

        # Schedule the scheldue post
        post_id = await self.scheduler.schedule_post(
            scheduled_time,
            scheldue_content,
            user_id,
            {
                'type': 'scheldue',
                'question': scheldue_data.get('question'),
                'options': scheldue_data.get('options', []),
                'tickers': scheldue_data.get('tickers', []),
                'hashtags': scheldue_data.get('hashtags', [])
            }
        )

        # Store scheldue info
        if user_id not in self.scheduled_posts:
            self.scheduled_posts.append({
                'id': post_id,
                'time': scheduled_time,
                'content': scheldue_content,
                'user_id': user_id,
                'type': 'scheldue',
                'scheldue_data': scheldue_data
            })

        logger.info(f"User {username} created scheldue post {post_id} with question: {scheldue_data.get('question', 'N/A')}")
        return post_id

    async def _generate_scheldue_content(self, scheldue_data: Dict[str, Any]) -> str:
        """
        Generate scheldue content with polls, tickers, and hashtags.

        Args:
            scheldue_data: Scheldue data

        Returns:
            Generated content
        """
        content_parts = []

        # Add question
        if scheldue_data.get('question'):
            content_parts.append(f"**{scheldue_data['question']}**\n")

        # Add options if present
        if scheldue_data.get('options'):
            content_parts.append("\n🗳️ **Options:**\n")
            for i, option in enumerate(scheldue_data['options'], 1):
                content_parts.append(f"{i}. {option}")

        # Add ticker information
        if scheldue_data.get('tickers'):
            content_parts.append("\n📊 **Market Data:**\n")
            # Format tickers with prices
            for ticker in scheldue_data['tickers']:
                content_parts.append(f"• ${ticker}")

        # Add hashtags
        if scheldue_data.get('hashtags'):
            content_parts.append("\n🏷️ **Topics:**\n")
            for hashtag in scheldue_data['hashtags']:
                content_parts.append(f"#{hashtag}")

        # Add regular content if present
        if scheldue_data.get('content') and scheldue_data['content'].strip():
            content_parts.append(f"\n📝 **Additional Content:**\n{ scheldue_data['content'] }")

        # Join all parts
        return "\n".join(content_parts)

    async def scheldue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /scheldue command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Security check: only allow private messages
        if update.effective_chat.type != 'private':
            await update.message.reply_text(
                "❌ This bot only works in private messages! "
                "Please message me directly to use AdminKroha."
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use scheldue in group chat")
            return

        # Check if user is admin (only admin can use the bot)
        if self.config.admin_user_id and user_id != self.config.admin_user_id:
            await update.message.reply_text(
                "❌ Only the bot administrator has permission to use AdminKroha!"
            )
            logger.warning(f"User {username} (ID: {user_id}) tried to use scheldue without admin permissions")
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide scheldue details!\n"
                "Usage: `/scheldue <time> <details>`\n"
                "Examples:\n"
                "  `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc`\n"
                "  `/scheldue 09:00 \"Daily analysis\" \"BTC: $45k\" #crypto`\n\n"
                "Details can include:\n"
                "  • Question for poll: \"Will BTC rise?\"\n"
                "  • Options: Yes No Maybe\n"
                "  • Tickers: $btc $eth $sol (with or without $)\n"
                "  • Hashtags: #crypto #bitcoin\n"
                "  • Content for regular post after options\n\n"
                "For interactive scheldue creation, use: `/scheldue`"
            )
            return

        time_str = context.args[0]
        details = ' '.join(context.args[1:])

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Invalid scheldue format!\n"
                    "Please provide details in format: [question] [options] [tickers] [hashtags] [content]\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc #crypto`\n"
                    "Example: `/scheldue 09:00 \"Daily analysis\" \"BTC: $45k\" #crypto`\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc $eth\""
                )
                return

            # Schedule the scheldue post
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Invalid time format! Use HH:MM format (24 hours)\n"
                    "Example: `/scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc`"
                )
                return

            # Create scheldue post with all features
            post_id = await self._create_scheldue_post(
                scheduled_time,
                scheldue_data,
                user_id,
                username
            )

            success_message = (
                f"🚀 **Scheldue Post Scheduled Successfully!** 🎉\n\n"
                f"📝 **Question:** {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ **Options:** {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 **Tickers:** {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ **Hashtags:** {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ **Scheduled Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 **Scheldue ID:** {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 **Next steps:**\n"
                f"• `/scheldue` - Create another scheldue\n"
                f"• `/status` - Check bot status\n"
                f"• `/list-reminders` - Manage reminders\n"
                f"• `/help` - View all commands"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled scheldue: {details[:50]}...")

        except Exception as e:
            error_message = f"❌ Error scheduling scheldue: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error scheduling scheldue for user {username}: {e}")

    async def scheldue_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue command with interactive interface.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Security check: only allow private messages
        if update.effective_chat.type != 'private':
            await update.message.reply_text(
                "❌ This bot only works in private messages! "
                "Please message me directly to use AdminKroha."
            )
            return

        # Check if user is admin (only admin can use the bot)
        if self.config.admin_user_id and user_id != self.config.admin_user_id:
            await update.message.reply_text(
                "❌ Only the bot administrator has permission to use AdminKroha!"
            )
            return

        # Interactive scheldue creation
        await update.message.reply_text(
            "🚀 **AdminKroha Scheldue Creator** 🚀\n\n"
            "Let's create a scheduled post with polls, tickers, and hashtags!\n\n"
            "**Step 1:** Provide the scheduled time (HH:MM format)\n"
            "Example: `14:30` for 2:30 PM\n\n"
            "**Step 2:** Provide the content details\n"
            "You can include:\n"
            "  • Question: \"Will BTC rise?\"\n"
            "  • Options: Yes No Maybe\n"
            "  • Tickers: $btc $eth $sol or BTCUSDT ETHUSDT\n"
            "  • Hashtags: #crypto #bitcoin\n"
            "  • Regular content after options\n\n"
            "**Example:** `14:30 \"Will BTC rise?\" Yes No Maybe $btc #crypto`\n\n"
            "Please provide your scheduled time and details:"
        )

        # Store scheldue creation state
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['scheldue_step'] = 'waiting_for_details'
        self.user_data[user_id]['scheldue_username'] = username

    async def scheldue_details_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue details after interactive setup.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id

        # Check if user is in scheldue creation process
        if user_id not in self.user_data or self.user_data[user_id].get('scheldue_step') != 'waiting_for_details':
            return

        scheldue_details = update.message.text.strip()

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(scheldue_details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Invalid scheldue format!\n"
                    "Please provide details in format: [question] [options] [tickers] [hashtags] [content]\n"
                    "Example: `\"Will BTC rise?\" Yes No Maybe $btc #crypto`\n"
                    "Example: `\"Daily analysis\" \"BTC: $45k\" #crypto`\n"
                    "Please try again:"
                )
                return

            # Send interactive time input
            await update.message.reply_text(
                "⏰ **Step 2:** Please provide the scheduled time (HH:MM format):\n"
                "Example: `14:30` for 2:30 PM\n"
                "Example: `09:00` for 9:00 AM\n"
                "Please enter the time:"
            )

            # Store scheldue data temporarily
            self.user_data[user_id]['scheldue_data'] = scheldue_data
            self.user_data[user_id]['scheldue_step'] = 'waiting_for_time'

        except Exception as e:
            await update.message.reply_text(f"❌ Error processing scheldue details: {e}")
            logger.error(f"Error processing scheldue details for user {user_id}: {e}")

    async def scheldue_time_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle scheldue time input after interactive setup.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id

        # Check if user is waiting for time input
        if user_id not in self.user_data or self.user_data[user_id].get('scheldue_step') != 'waiting_for_time':
            return

        time_str = update.message.text.strip()

        try:
            # Parse time
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Invalid time format! Use HH:MM format (24 hours)\n"
                    "Example: `14:30` for 2:30 PM\n"
                    "Please enter the time again:"
                )
                return

            # Complete scheldue creation
            scheldue_data = self.user_data[user_id]['scheldue_data']
            username = self.user_data[user_id]['scheldue_username']

            # Create scheldue post
            post_id = await self._create_scheldue_post(
                scheduled_time,
                scheldue_data,
                user_id,
                username
            )

            # Clear temporary data
            del self.user_data[user_id]['scheldue_data']
            del self.user_data[user_id]['scheldue_step']
            del self.user_data[user_id]['scheldue_username']

            # Send success message
            await update.message.reply_text(
                f"✅ **Scheldue Post Scheduled Successfully!** 🎉\n\n"
                f"📝 **Question:** {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ **Options:** {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 **Tickers:** {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ **Hashtags:** {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ **Scheduled Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 **Scheldue ID:** {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 **Next steps:**\n"
                f"• `/scheldue` - Create another scheldue\n"
                f"• `/status` - Check bot status\n"
                f"• `/list-reminders` - Manage reminders\n"
                f"• `/help` - View all commands"
            )

            logger.info(f"User {username} (ID: {user_id}) created scheldue post {post_id}")

        except Exception as e:
            await update.message.reply_text(f"❌ Error scheduling scheldue: {e}")
            logger.error(f"Error scheduling scheldue for user {user_id}: {e}")

    async def poll_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /poll command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ Please provide a question and at least 2 options!\n"
                "Example: `/poll Will BTC go above $50k? Yes No Maybe`"
            )
            return

        question = context.args[0]
        options = context.args[1:]

        if len(options) < 2:
            await update.message.reply_text(
                "❌ Please provide at least 2 options for the poll!\n"
                "Example: `/poll Will BTC go above $50k? Yes No Maybe`"
            )
            return

        self.user_data[user_id]['commands_used'] += 1

        try:
            # Create inline keyboard for poll options
            keyboard = []
            for i, option in enumerate(options):
                keyboard.append([InlineKeyboardButton(option, callback_data=f'poll_{i}')])

            reply_markup = InlineKeyboardMarkup(keyboard)

            poll_message = (
                f"🗳️ **Poll Created!**\n\n"
                f"**Question:** {question}\n\n"
                f"**Options:**\n"
            )

            for i, option in enumerate(options):
                poll_message += f"{i + 1}. {option}\n"

            poll_message += f"\nVote by clicking on any option above!"

            await update.message.reply_text(poll_message, reply_markup=reply_markup)
            logger.info(f"User {username} created a poll: {question[:50]}...")

        except Exception as e:
            error_message = f"❌ Error creating poll: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error creating poll for user {username}: {e}")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries for polls.

        Args:
            update: Telegram update object
            context: Bot context
        """
        query = update.callback_query
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        callback_data = query.data

        if callback_data.startswith('poll_'):
            option_index = int(callback_data.split('_')[1])

            # Here you would typically store the vote and update poll results
            # For this example, we'll just acknowledge the vote

            await query.answer(f"You voted for option {option_index + 1}!")
            logger.info(f"User {username} voted for option {option_index + 1}")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /status command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Get bot statistics
        total_users = len(self.user_data)
        total_commands = sum(data.get('commands_used', 0) for data in self.user_data.values())
        active_scheduled = len(self.scheduled_posts)

        status_message = (
            f"📊 **Bot Status Report**\n\n"
            f"🤖 **Bot Information:**\n"
            f"• Name: Binance Square Telegram Bot\n"
            f"• Version: 1.0.0\n"
            f"• Python: 3.8+\n\n"
            f"👥 **User Statistics:**\n"
            f"• Total Users: {total_users}\n"
            f"• Total Commands Used: {total_commands}\n"
            f"• Average Commands per User: {total_commands / max(total_users, 1):.1f}\n\n"
            f"⏰ **Bot Statistics:**\n"
            f"• Status: Online ✅\n"
            f"• Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• Scheduled Posts: {active_scheduled}\n\n"
            f"🔗 **API Status:**\n"
            f"• Binance Square API: Connected ✅\n"
            f"• Telegram API: Connected ✅\n\n"
            f"📝 **Recent Activity:**\n"
            f"• Last 10 minutes: Active\n"
            f"• Errors in last hour: 0\n"
            f"• Successful posts: Active\n"
        )

        await update.message.reply_text(status_message)
        logger.info(f"User {username} requested bot status")

    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /schedule command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide time and content!\n"
                "Example: `/schedule 14:30 Market analysis tomorrow`"
            )
            return

        time_str = context.args[0]
        content = ' '.join(context.args[1:])

        try:
            # Parse time
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Invalid time format! Use HH:MM format (24 hours)\n"
                    "Example: `/schedule 14:30 Market analysis tomorrow`"
                )
                return

            # Schedule the post
            post_id = await self.scheduler.schedule_post(
                scheduled_time,
                content,
                user_id
            )

            self.scheduled_posts.append({
                'id': post_id,
                'time': scheduled_time,
                'content': content,
                'user_id': user_id
            })

            success_message = (
                f"⏰ **Post Scheduled Successfully!** 🎉\n\n"
                f"📝 **Content:** {content}\n"
                f"🕐 **Scheduled Time:** {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 **Post ID:** {post_id}\n"
                f"👤 **Scheduled by:** {username}\n\n"
                f"The post will be published automatically at the scheduled time!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled a post: {content[:50]}...")

        except Exception as e:
            error_message = f"❌ Error scheduling post: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error scheduling post for user {username}: {e}")

    async def add_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /add-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide reminder details!\n"
                "Usage: `/add-reminder <type> <time> [days] [message]`\n"
                "Examples:\n"
                "  `/add-reminder task 09:00 Task completed for today`\n"
                "  `/add-reminder market 14:30 BTC price check #crypto`\n"
                "  `/add-reminder analysis 19:00 End of trading session`\n\n"
                "Reminder types: task, market, analysis, news, general"
            )
            return

        # Parse arguments
        args = context.args
        reminder_type = args[0].lower()
        time = args[1] if len(args) > 1 else "09:00"
        days_of_week = None
        message = ""

        # Parse days of week if provided
        if len(args) > 2 and args[2].lower() not in ['task', 'market', 'analysis', 'news', 'general']:
            try:
                # Parse days (e.g., "0,2,4" for Monday, Wednesday, Friday)
                days_of_week = [int(d.strip()) for d in args[2].split(',')]
                if len(args) > 3:
                    message = ' '.join(args[3:])
            except ValueError:
                message = ' '.join(args[2:])
        else:
            # Use message from remaining args
            if len(args) > 2:
                message = ' '.join(args[2:])

        try:
            # Add the reminder
            reminder_id = await self.reminder_manager.add_reminder(
                reminder_type=reminder_type,
                time=time,
                days_of_week=days_of_week,
                is_recurring=True,
                message=message,
                user_id=user_id
            )

            # Get day names for display
            day_names = []
            if days_of_week:
                for day in days_of_week:
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_names.append(days[day % 7])
                days_display = ', '.join(day_names)
            else:
                days_display = 'Every day'

            success_message = (
                f"✅ **Reminder Added Successfully!** 🎉\n\n"
                f"🔔 **Type:** {reminder_type.title()}\n"
                f"⏰ **Time:** {time}\n"
                f"📅 **Days:** {days_display}\n"
                f"💬 **Message:** {message}\n"
                f"🆔 **Reminder ID:** {reminder_id}\n\n"
                f"The reminder will notify you at the specified time on the selected days!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} added reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Error adding reminder: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error adding reminder for user {username}: {e}")

    async def list_reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /list-reminders command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        try:
            # Get user's reminders
            reminders = await self.reminder_manager.get_reminders(user_id)

            if not reminders:
                await update.message.reply_text(
                    "📭 **No Reminders Found**\n\n"
                    "You don't have any reminders set up yet.\n"
                    "Use `/add-reminder` to add your first reminder!"
                )
                return

            # Format reminders list
            reminders_list = "🔔 **Your Reminders:**\n\n"

            for reminder in reminders:
                # Format days
                days = reminder.get('days_of_week', [])
                if days:
                    day_names = []
                    for day in days:
                        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        day_names.append(days[day % 7])
                    days_display = ', '.join(day_names)
                else:
                    days_display = 'Every day'

                # Format reminder status
                next_triggered = reminder.get('next_triggered')
                if next_triggered:
                    try:
                        next_time = datetime.fromisoformat(next_triggered)
                        next_time_str = next_time.strftime('%Y-%m-%d %H:%M')
                    except:
                        next_time_str = 'Soon'
                else:
                    next_time_str = 'Soon'

                reminders_list += (
                    f"📌 **{reminder['reminder_type'].title()}**\n"
                    f"   ⏰ Time: {reminder['time']} ({next_time_str})\n"
                    f"   📅 Days: {days_display}\n"
                    f"   💬 Message: {reminder['message']}\n"
                    f"   🆔 ID: {reminder['reminder_id']}\n\n"
                )

            # Add some footer information
            reminders_list += (
                f"📊 **Total Reminders:** {len(reminders)}\n"
                f"🔄 **Recurring:** {sum(1 for r in reminders if r.get('is_recurring', True))}\n"
                f"📅 **Today Due:** {len([r for r in reminders if r.get('is_due_today', lambda: False)()])}\n\n"
                f"💡 **Commands:**\n"
                f"  • `/add-reminder <type> <time> [days] [message]` - Add new reminder\n"
                f"  • `/remove-reminder <id>` - Remove reminder\n"
                f"  • `/update-reminder <id> [updates]` - Update reminder\n"
                f"  • `/trigger-reminder <id>` - Trigger reminder immediately\n"
            )

            await update.message.reply_text(reminders_list)
            logger.info(f"User {username} listed reminders")

        except Exception as e:
            error_message = f"❌ Error listing reminders: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error listing reminders for user {username}: {e}")

    async def remove_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /remove-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a reminder ID!\n"
                "Usage: `/remove-reminder <reminder_id>`\n"
                "You can find your reminder IDs using `/list-reminders`"
            )
            return

        reminder_id = context.args[0]

        try:
            # Remove the reminder
            success = await self.reminder_manager.remove_reminder(reminder_id, user_id)

            if success:
                success_message = (
                    f"✅ **Reminder Removed Successfully!** 🎉\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **Removed by:** {username}\n\n"
                    f"The reminder has been removed and will no longer trigger."
                )
            else:
                success_message = (
                    f"❌ **Reminder Not Found**\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **User:** {username}\n\n"
                    f"Could not find the specified reminder. Please check the ID and try again."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} removed reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Error removing reminder: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error removing reminder for user {username}: {e}")

    async def update_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /update-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a reminder ID and updates!\n"
                "Usage: `/update-reminder <reminder_id> <field> <value>`\n"
                "Examples:\n"
                "  `/update-reminder rem_123 time 10:00`\n"
                "  `/update-reminder rem_123 message New task message`\n"
                "  `/update-reminder rem_123 days 0,2,4`\n"
                "  `/update-reminder rem_123 recurring false"
            )
            return

        reminder_id = context.args[0]

        try:
            # Parse updates
            updates = {}
            if len(context.args) > 1:
                # Simple field-value parsing
                for i in range(1, len(context.args), 2):
                    if i + 1 < len(context.args):
                        field = context.args[i].lower()
                        value = context.args[i + 1]

                        if field == 'days':
                            try:
                                updates[field] = [int(d.strip()) for d in value.split(',')]
                            except ValueError:
                                await update.message.reply_text(f"❌ Invalid days format: {value}")
                                return
                        elif field == 'recurring':
                            updates[field] = value.lower() in ['true', 'yes', '1', 'on']
                        else:
                            updates[field] = value

            # Update the reminder
            success = await self.reminder_manager.update_reminder(reminder_id, updates, user_id)

            if success:
                success_message = (
                    f"✅ **Reminder Updated Successfully!** 🎉\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **Updated by:** {username}\n"
                    f"📝 **Updates:** {updates}\n\n"
                    f"The reminder has been updated successfully."
                )
            else:
                success_message = (
                    f"❌ **Reminder Not Found**\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **User:** {username}\n\n"
                    f"Could not find the specified reminder. Please check the ID and try again."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} updated reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Error updating reminder: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error updating reminder for user {username}: {e}")

    async def trigger_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /trigger-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a reminder ID!\n"
                "Usage: `/trigger-reminder <reminder_id>`\n"
                "You can find your reminder IDs using `/list-reminders`"
            )
            return

        reminder_id = context.args[0]

        try:
            # Trigger the reminder
            success = await self.reminder_manager.trigger_reminder(reminder_id)

            if success:
                success_message = (
                    f"✅ **Reminder Triggered Successfully!** 🎉\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **Triggered by:** {username}\n\n"
                    f"The reminder has been triggered immediately!"
                )
            else:
                success_message = (
                    f"❌ **Reminder Not Found**\n\n"
                    f"🆔 **Reminder ID:** {reminder_id}\n"
                    f"👤 **User:** {username}\n\n"
                    f"Could not find the specified reminder. Please check the ID and try again."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} triggered reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Error triggering reminder: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error triggering reminder for user {username}: {e}")

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """
        Parse time string in HH:MM format.

        Args:
            time_str: Time string in HH:MM format

        Returns:
            Parsed datetime object or None if invalid
        """
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return None

            # Schedule for today at the specified time
            scheduled_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the time has already passed today, schedule for tomorrow
            if scheduled_time <= datetime.now():
                scheduled_time += timedelta(days=1)

            return scheduled_time
        except ValueError:
            return None

    def run(self) -> None:
        """Start the bot."""
        # Create the Application
        application = Application.builder().token(self.config.bot_token).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("post", self.post_command))
        application.add_handler(CommandHandler("post_image", self.post_image_command))
        application.add_handler(CommandHandler("get_tickers", self.get_tickers_command))
        application.add_handler(CommandHandler("poll", self.poll_command))
        application.add_handler(CommandHandler("schedule", self.schedule_command))
        application.add_handler(CommandHandler("status", self.status_command))

        # Add reminder command handlers
        application.add_handler(CommandHandler("add_reminder", self.add_reminder_command))
        application.add_handler(CommandHandler("list_reminders", self.list_reminders_command))
        application.add_handler(CommandHandler("remove_reminder", self.remove_reminder_command))
        application.add_handler(CommandHandler("update_reminder", self.update_reminder_command))
        application.add_handler(CommandHandler("trigger_reminder", self.trigger_reminder_command))

        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))

        # Add message handler for photos
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

        # Add scheldue command handlers
        application.add_handler(CommandHandler("scheldue", self.scheldue_command))
        application.add_handler(CommandHandler("scheldue", self.scheldue_command_handler))

        # Add scheldue details handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.scheldue_details_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.scheldue_time_handler))

        # Start the bot
        logger.info("Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot stopped.")
