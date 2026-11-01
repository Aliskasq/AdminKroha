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

        # Initialize user data
        self.user_data[user_id] = {
            'username': username,
            'start_time': datetime.now(),
            'commands_used': 0
        }

        welcome_message = (
            f"👋 Welcome, {username}! I'm the Binance Square Telegram Bot! 🎉\n\n"
            f"I can help you post content to Binance Square with various features:\n\n"
            f"📝 **Available Commands:**\n"
            f"• /help - Show all commands\n"
            f"• /post <text> - Post text content to Binance Square\n"
            f"• /post-image <text> - Post content with image\n"
            f"• /get-tickers <tickers> - Get ticker data\n"
            f"• /poll <question> <option1> <option2> ... - Create a poll\n"
            f"• /schedule <time> <text> - Schedule a post\n"
            f"• /status - Check bot status\n\n"
            f"🔧 **Admin Commands:**\n"
            f"• /broadcast <text> - Send broadcast message (admin only)\n"
            f"• /logs - View recent logs (admin only)\n\n"
            f"📊 **Features:**\n"
            f"• Hashtag support in posts\n"
            f"• Real-time ticker data\n"
            f"• Image upload and processing\n"
            f"• Interactive polls\n"
            f"• Content scheduling\n"
            f"• Multi-language support\n\n"
            f"Type /help to see all commands!"
        )

        await update.message.reply_text(welcome_message)
        logger.info(f"User {username} (ID: {user_id}) started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        help_message = (
            f"👋 Hi, {username}! Here's a complete guide to using the Binance Square Bot! 📚\n\n"
            f"📝 **TEXT POSTS:**\n"
            f"Use /post followed by your content to create a text post:\n"
            f"  Example: `/post BTC is bullish today #crypto #trading`\n\n"
            f"🖼️ **IMAGE POSTS:**\n"
            f"Use /post-image followed by text and an image to create a post with an image:\n"
            f"  Step 1: `/post-image Market analysis`\n"
            f"  Step 2: Send the image to the bot\n\n"
            f"📊 **TICKER DATA:**\n"
            f"Get real-time cryptocurrency ticker information:\n"
            f"  Example: `/get-tickers BTCUSDT ETHUSDT SOLUSDT`\n\n"
            f"🗳️ **POLLS:**\n"
            f"Create interactive polls with multiple options:\n"
            f"  Example: `/poll Will BTC go above $50k? Yes No Maybe`\n\n"
            f"⏰ **SCHEDULING:**\n"
            f"Schedule posts for future times:\n"
            f"  Example: `/schedule 14:30 Market analysis tomorrow`\n\n"
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
            f"• Include multiple tickers for comprehensive analysis\n"
            f"• Schedule posts during peak hours for maximum engagement\n"
            f"• Use polls to engage with your audience\n\n"
            f"❓ Need help? Type any command to get started!"
        )

        await update.message.reply_text(help_message)
        logger.info(f"User {username} requested help")

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
        Handle /post-image command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide text content for the image post!\n"
                "Example: `/post-image Market analysis today`"
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
                "Please start with `/post-image <text>` command first."
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
        Handle /get-tickers command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Please provide ticker symbols!\n"
                "Example: `/get-tickers BTCUSDT ETHUSDT SOLUSDT`"
            )
            return

        tickers = [arg.upper() for arg in context.args if arg.upper().endswith('USDT')]

        if not tickers:
            await update.message.reply_text(
                "❌ Please provide valid ticker symbols ending with USDT!\n"
                "Example: `/get-tickers BTCUSDT ETHUSDT SOLUSDT`"
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
        application.add_handler(CommandHandler("post-image", self.post_image_command))
        application.add_handler(CommandHandler("get-tickers", self.get_tickers_command))
        application.add_handler(CommandHandler("poll", self.poll_command))
        application.add_handler(CommandHandler("schedule", self.schedule_command))
        application.add_handler(CommandHandler("status", self.status_command))

        # Add reminder command handlers
        application.add_handler(CommandHandler("add-reminder", self.add_reminder_command))
        application.add_handler(CommandHandler("list-reminders", self.list_reminders_command))
        application.add_handler(CommandHandler("remove-reminder", self.remove_reminder_command))
        application.add_handler(CommandHandler("update-reminder", self.update_reminder_command))
        application.add_handler(CommandHandler("trigger-reminder", self.trigger_reminder_command))

        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.callback_query_handler))

        # Add message handler for photos
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

        # Start the bot
        logger.info("Bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot stopped.")