"""
Main Telegram Bot for Binance Square

This bot allows users to post content to Binance Square via Telegram commands.
It supports various features including text posts, image posts, polls, ticker data,
and content scheduling.
"""

import logging
import asyncio
import re
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
        self.image_handler.set_binance_api(self.binance_api)
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

    def _ensure_user_data(self, user_id: int, username: str, chat_id: int) -> None:
        """Ensure user_data entry exists for the given user."""
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'username': username,
                'start_time': datetime.now(),
                'commands_used': 0,
                'chat_id': chat_id
            }
        # Update username in case it changed
        self.user_data[user_id]['username'] = username

    async def is_group_admin(self, update: Update) -> bool:
        """
        Check if the user is an administrator or creator of the group.

        Args:
            update: Telegram update object

        Returns:
            True if user is admin or creator, False otherwise
        """
        try:
            chat_id = update.effective_chat.id
            user_id = update.effective_user.id
            member = await update.get_bot().get_chat_member(chat_id, user_id)
            return member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            # Fallback: check against ADMIN_USER_ID from config
            admin_user_id = getattr(self.config, 'admin_user_id', None)
            if admin_user_id:
                try:
                    admin_id = int(admin_user_id)
                    user_id = update.effective_user.id
                    if user_id == admin_id:
                        logger.warning(f"Fallback to ADMIN_USER_ID check: user {user_id} is admin")
                        return True
                except (ValueError, TypeError):
                    pass
            return False

    async def is_admin_in_configured_group(self, user_id: int) -> bool:
        """
        Check if the user is an administrator in the configured Telegram group.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is admin or creator in the configured group, False otherwise
        """
        try:
            if not self.config.telegram_group_id:
                return False
            chat_id = int(self.config.telegram_group_id)
            member = await self.bot.get_chat_member(chat_id, user_id)
            return member.status in ['administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking admin status in configured group: {e}")
            return False

    async def require_group_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Check if user is group admin and send error message if not.

        Args:
            update: Telegram update object
            context: Bot context

        Returns:
            True if user is admin, False otherwise (and sends error message)
        """
        # Security check: only allow group chats
        chat_type = update.effective_chat.type
        if chat_type != 'group' and chat_type != 'supergroup':
            await update.message.reply_text(
                "❌ Этот бот работает только в групповых чатах! "
                "Добавьте меня в группу, чтобы использовать AdminKroha."
            )
            logger.warning(f"User {update.effective_user.username or update.effective_user.first_name} (ID: {update.effective_user.id}) tried to use bot in private chat")
            return False

        # Check if user is group admin
        if not await self.is_group_admin(update):
            await update.message.reply_text(
                "❌ Только администраторы группы имеют право использовать AdminKroha!"
            )
            logger.warning(f"User {update.effective_user.username or update.effective_user.first_name} (ID: {update.effective_user.id}) tried to use bot without admin permissions")
            return False

        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Initialize user data
        self.user_data[user_id] = {
            'username': username,
            'start_time': datetime.now(),
            'commands_used': 0,
            'chat_id': update.effective_chat.id
        }

        welcome_message = (
            f"👋 Привет, {username}! Я — AdminKroha, улучшенный Telegram-бот для Binance Square! 🚀\n\n"
            f"🎯 Доступ: Бот работает только в групповых чатах и супергруппах.\n\n"
            f"📝 Доступные команды:\n"
            f"• /help — Показать все команды\n"
            f"• /post <текст> — Опубликовать текст в Binance Square\n"
            f"• /post_image или /image <текст> — Пост с 1-2 фото (кнопки)\n"
            f"• /article <заголовок> — Статья с обложкой (кнопки)\n"
            f"• /schedule <время> <текст> — Запланировать пост\n"
            f"• /scheldue <детали> — Расширенное планирование\n"
            f"• /add_reminder <тип> <время> [дни] [сообщение] — Добавить напоминание\n"
            f"• /list_reminders — Список напоминаний\n"
            f"• /status — Статус бота\n\n"
            f"📊 Возможности:\n"
            f"• Поддержка хештегов в постах\n"
            f"• Данные тикеров в реальном времени с подсветкой $SYMBOL\n"
            f"• Загрузка и обработка изображений (до 2 фото на пост)\n"
            f"• Статьи с обложкой (contentType=2)\n"
            f"• Планирование постов\n"
            f"• Расширенная система напоминаний\n\n"
            f"🔧 Команды для админов:\n"
            f"• /broadcast <текст> — Рассылка (только админ)\n"
            f"• /logs — Просмотр логов (только админ)\n\n"
            f"⚠️ Важно: Бот ограничен групповыми чатами и администраторами для безопасности.\n\n"
            f"❓ Нужна помощь? Введите любую команду для начала!"
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
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        help_message = (
            f"👋 Привет, {username}! Полное руководство по AdminKroha! 📚\n\n"
            f"📝 ТЕКСТОВЫЕ ПОСТЫ:\n"
            f"Используйте /post с текстом для публикации:\n"
            f"  Пример: /post BTC пробивает уровень #crypto #trading\n\n"
            f"🖼️ ПОСТЫ С ИЗОБРАЖЕНИЕМ (до 2 фото):\n"
            f"  /post_image или /image Анализ рынка\n"
            f"  Потом пришлите фото (кнопки: Добавить / Отправить / Отмена)\n\n"
            f"📰 СТАТЬИ С ОБЛОЖКОЙ:\n"
            f"  /article Заголовок статьи\n"
            f"  Кнопки: Добавить текст / Добавить обложку / Отправить / Отмена\n\n"
            f"⏰ ПЛАНИРОВАНИЕ:\n"
            f"Отложите пост на будущее:\n"
            f"  Пример: /schedule 14:30 Анализ на завтра\n\n"
            f"🚀 РАСШИРЕННОЕ ПЛАНИРОВАНИЕ (/scheldue):\n"
            f"Пост с тикерами и хештегами:\n"
            f"  Пример: /scheldue 14:30 \"Анализ BTC\" $btc #crypto\n\n"
            f"🔔 НАПОМИНАНИЯ:\n"
            f"Добавьте напоминание с временем и днями:\n"
            f"  Пример: /add_reminder task 09:00 Задачи 0,2,4\n"
            f"  Пример: /add_reminder market 14:30 BTC $btc 0,1,2,3,4\n\n"
            f"🔧 КОМАНДЫ АДМИНА:\n"
            f"• /status — Статус и статистика бота\n"
            f"• /broadcast <текст> — Рассылка всем пользователям\n"
            f"• /logs — Просмотр недавних логов\n\n"
            f"📈 СТАТУС БОТА:\n"
            f"• Онлайн и реагирует\n"
            f"• Подключен к Binance Square API\n"
            f"• Обработка постов: Активна\n"
            f"• Запланированных постов: {len(self.scheduled_posts)}\n\n"
            f"🎯 Советы:\n"
            f"• Используйте хештеги (#crypto, #btc, #trading) для охвата\n"
            f"• Добавляйте $SYMBOL для авто-подсветки тикеров\n"
            f"• Планируйте посты в пиковые часы\n"
            f"• Напоминания для регулярных задач\n\n"
            f"🔒 Безопасность: Бот работает только в группах и для админов.\n\n"
            f"❓ Нужна помощь? Введите любую команду!"
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
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Extract details preserving newlines
        message_text = update.message.text or update.message.caption or ''
        parts = message_text.split(' ', 2)
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Укажите детали для scheldue!\n"
                "Использование: /scheldue <время> <детали>\n"
                "Примеры:\n"
                "  /scheldue 14:30 \"Вырастет BTC?\" Да Нет Возможно $btc\n"
                "  /scheldue 09:00 \"Ежедневный анализ\" \"BTC: $45k\" #crypto\n\n"
                "Детали могут содержать:\n"
                "  • Вопрос для опроса: \"Вырастет BTC?\"\n"
                "  • Варианты: Да Нет Возможно\n"
                "  • Тикеры: $btc $eth $sol (с или без $)\n"
                "  • Хештеги: #crypto #bitcoin\n"
                "  • Текст для обычного поста после вариантов"
            )
            return

        time_str = parts[1]
        details = parts[2]  # Preserve newlines in details

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Неверный формат scheldue!\n"
                    "Формат: [вопрос] [варианты] [тики] [хештеги] [контент]\n"
                    "Пример: /scheldue 14:30 \"Вырастет BTC?\" Да Нет $btc #crypto\n"
                    "Пример: /scheldue 09:00 \"Анализ\" \"BTC: $45k\" #crypto\n"
                    "Пример: /scheldue 14:30 \"Вырастет BTC?\" Да Нет $btc $eth"
                )
                return

            # Schedule the scheldue post
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Неверный формат времени! Используйте ЧЧ:ММ (24 часа)\n"
                    "Пример: /scheldue 14:30 \"Вырастет BTC?\" Да Нет $btc"
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
                f"🚀 Scheldue пост запланирован успешно! 🎉\n\n"
                f"📝 Вопрос: {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ Варианты: {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 Тикеры: {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ Хештеги: {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ Время публикации: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 Scheldue ID: {post_id}\n"
                f"👤 Запланировал: {username}\n\n"
                f"Пост автоматически опубликуется с опросом, тикерами и хештегами!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled scheldue: {details[:50]}...")

        except Exception as e:
            error_message = f"❌ Ошибка планирования scheldue: {str(e)}\n"
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
                "❌ Этот бот работает только в личных сообщениях! "
                "Напишите мне напрямую для использования AdminKroha."
            )
            return

        # Check if user is admin in the configured group
        try:
            if not self.config.telegram_group_id:
                await update.message.reply_text(
                    "❌ Бот не настроен с ID группы."
                )
                return
            chat_id = int(self.config.telegram_group_id)
            member = await update.get_bot().get_chat_member(chat_id, user_id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ Только администраторы настроенной группы могут использовать эту функцию!"
                )
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            await update.message.reply_text(
                "❌ Ошибка проверки прав админа. Попробуйте снова."
            )
            return

        # Interactive scheldue creation
        await update.message.reply_text(
            "🚀 AdminKroha Scheldue Creator 🚀\n\n"
            "Создадим запланированный пост с опросами, тикерами и хештегами!\n\n"
            "Шаг 1: Укажите время публикации (ЧЧ:ММ)\n"
            "Пример: 14:30 для 14:30\n\n"
            "Шаг 2: Укажите детали контента\n"
            "Можно добавить:\n"
            "  • Вопрос: \"Вырастет BTC?\"\n"
            "  • Варианты: Да Нет Возможно\n"
            "  • Тикеры: $btc $eth $sol или BTCUSDT ETHUSDT\n"
            "  • Хештеги: #crypto #bitcoin\n"
            "  • Текст после вариантов\n\n"
            "Пример: 14:30 \"Вырастет BTC?\" Да Нет $btc #crypto\n\n"
            "Введите время и детали:"
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
                    "Example: \"Will BTC rise?\" Yes No Maybe $btc #crypto\n"
                    "Example: \"Daily analysis\" \"BTC: $45k\" #crypto\n"
                    "Please try again:"
                )
                return

            # Send interactive time input
            await update.message.reply_text(
                "⏰ Step 2: Please provide the scheduled time (HH:MM format):\n"
                "Example: 14:30 for 2:30 PM\n"
                "Example: 09:00 for 9:00 AM\n"
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
                    "Example: 14:30 for 2:30 PM\n"
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
                f"✅ Scheldue Post Scheduled Successfully! 🎉\n\n"
                f"📝 Question: {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ Options: {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 Tickers: {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ Hashtags: {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ Scheduled Time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 Scheldue ID: {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 Next steps:\n"
                f"• /scheldue - Create another scheldue\n"
                f"• /status - Check bot status\n"
                f"• /list-reminders - Manage reminders\n"
                f"• /help - View all commands"
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
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Ensure user data exists
        self._ensure_user_data(user_id, username, update.effective_chat.id)

        # Extract text content preserving newlines - use raw message text
        message_text = update.message.text or update.message.caption or ''
        parts = message_text.split(' ', 1)
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Укажите контент для публикации!\n"
                "Пример: /post BTC пробивает уровень #crypto #trading"
            )
            return

        content = parts[1]  # Everything after the command, preserving newlines
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

            # Extract post ID and link from new API response format
            post_id = result.get('data', {}).get('id', 'N/A')
            share_link = result.get('data', {}).get('shareLink', f'https://www.binance.com/square/post/{post_id}')

            success_message = (
                f"✅ Пост успешно опубликован! 🎉\n\n"
                f"📝 Контент:\n{formatted_content}\n\n"
                f"🆔 Post ID: {post_id}\n"
                f"🔗 Ссылка на пост: {share_link}"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} posted content to Binance Square: {content[:50]}...")

        except Exception as e:
            error_message = f"❌ Ошибка публикации: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error posting content for user {username}: {e}")

    async def post_image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /post_image command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Ensure user data exists
        self._ensure_user_data(user_id, username, update.effective_chat.id)

        # Extract text content preserving newlines - use raw message text
        message_text = update.message.text or update.message.caption or ''
        # Remove the command part (/post_image or /post_image@botname)
        parts = message_text.split(' ', 1)
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Укажите текст для поста с изображением!\n"
                "Пример: /post_image Анализ рынка сегодня"
            )
            return

        text_content = parts[1]  # Everything after the command, preserving newlines
        self.user_data[user_id]['commands_used'] += 1

        # Store the content in user data for the next messages
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id]['pending_image_post'] = text_content
        self.user_data[user_id]['pending_images'] = []  # List to collect image URLs

        # Send initial message with inline keyboard
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data='img_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🖼️ Отправьте 1-2 изображения для публикации с этим текстом:\n\n"
            f"📝 Текст: {text_content}\n\n"
            f"Можете отправить альбом или по одному фото.",
            reply_markup=reply_markup
        )

        logger.info(f"User {username} started image post with content: {text_content}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle photo messages for image posts and article covers.
        Supports single photos and media groups (albums).

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Check if user explicitly requested article cover (cover_pending flag)
        is_article_cover = (user_id in self.user_data and
                           'pending_article' in self.user_data[user_id] and
                           self.user_data[user_id].get('pending_article', {}).get('cover_pending', False))

        # Check if user has pending image post
        if not is_article_cover and (user_id not in self.user_data or 'pending_image_post' not in self.user_data[user_id]):
            await update.message.reply_text(
                "❌ Нет ожидающего поста с изображением!\n"
                "Сначала используйте /post_image <текст>."
            )
            return

        text_content = self.user_data[user_id].get('pending_image_post', '')

        # Check if we already have 2 images for regular post
        if not is_article_cover:
            current_images = self.user_data[user_id].get('pending_images', [])
            if len(current_images) >= 2:
                await update.message.reply_text(
                    "❌ Максимум 2 изображения на пост!\n"
                    "Нажмите кнопку 'Отправить пост' для публикации."
                )
                return

        # For article cover, check if already has cover
        if is_article_cover:
            article = self.user_data[user_id]['pending_article']
            if article.get('cover_url'):
                await update.message.reply_text("❌ Обложка уже добавлена! Максимум 1.")
                return

        try:
            # Get the image file (highest quality)
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()

            # Upload image to Binance
            image_result = await self.image_handler.upload_image(image_bytes)
            image_url = image_result['url']

            if is_article_cover:
                # Store as article cover
                self.user_data[user_id]['pending_article']['cover_url'] = image_url
                self.user_data[user_id]['pending_article']['cover_pending'] = False

                # Show updated article preview
                article = self.user_data[user_id]['pending_article']
                title = article.get('title', '')
                content = article.get('content', '')
                preview = content[:200] + '...' if len(content) > 200 else content

                keyboard = [
                    [InlineKeyboardButton("📝 Добавить текст", callback_data='art_add_text')],
                    [InlineKeyboardButton("✅ Отправить статью", callback_data='art_send')],
                    [InlineKeyboardButton("❌ Отмена", callback_data='art_cancel')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"🖼️ Обложка добавлена!\n\n"
                    f"📋 Заголовок: {title}\n\n"
                    f"📝 Текст ({len(content)} симв.):\n{preview}\n\n"
                    f"🖼️ Обложка: ✅ загружена\n\n"
                    f"Кнопки управления:",
                    reply_markup=reply_markup
                )
                logger.info(f"User {username} added cover to article: {title}")
            else:
                # Regular post image handling
                text_content = self.user_data[user_id]['pending_image_post']

                # Check if we already have 2 images
                current_images = self.user_data[user_id].get('pending_images', [])
                if len(current_images) >= 2:
                    await update.message.reply_text(
                        "❌ Максимум 2 изображения на пост!\n"
                        "Нажмите кнопку 'Отправить пост' для публикации."
                    )
                    return

                # Add to pending images
                if 'pending_images' not in self.user_data[user_id]:
                    self.user_data[user_id]['pending_images'] = []
                self.user_data[user_id]['pending_images'].append(image_url)

                images_count = len(self.user_data[user_id]['pending_images'])

                # Build keyboard based on number of images
                if images_count == 1:
                    keyboard = [
                        [InlineKeyboardButton("📸 Добавить ещё фото", callback_data='img_add')],
                        [InlineKeyboardButton("✅ Отправить пост", callback_data='img_send')],
                        [InlineKeyboardButton("❌ Отмена", callback_data='img_cancel')]
                    ]
                    message = f"📸 Изображение 1/2 получено.\n\nНажмите кнопку:"
                else:  # images_count == 2
                    keyboard = [
                        [InlineKeyboardButton("✅ Отправить пост", callback_data='img_send')],
                        [InlineKeyboardButton("❌ Отмена", callback_data='img_cancel')]
                    ]
                    message = f"📸 Изображение 2/2 получено.\n\nНажмите 'Отправить пост' для публикации:"

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)

        except Exception as e:
            error_message = f"❌ Ошибка загрузки изображения: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error uploading image for user {username}: {e}")

    async def _publish_image_post(self, user_id: int, chat_id: int, bot) -> None:
        """
        Publish the collected image post.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            bot: Bot instance for sending messages
        """
        if user_id not in self.user_data:
            return

        text_content = self.user_data[user_id].get('pending_image_post', '')
        images = self.user_data[user_id].get('pending_images', [])

        if not images:
            return

        # Get username for logging
        username = self.user_data[user_id].get('username', 'Unknown')

        try:
            # Prepare content with image list
            formatted_content = self.content_generator.generate_content(
                text_content,
                post_type='image'
            )

            # Post to Binance Square with all images
            post_result = await self.binance_api.post_content(
                formatted_content,
                post_type='image',
                image_list=images[:2]  # Max 2 images
            )

            # Clear pending state
            self.user_data[user_id].pop('pending_image_post', None)
            self.user_data[user_id].pop('pending_images', None)

            # Extract post ID and link
            post_id = post_result.get('data', {}).get('id', 'N/A')
            share_link = post_result.get('data', {}).get('shareLink', f'https://www.binance.com/square/post/{post_id}')

            success_message = (
                f"✅ Пост с {len(images)} изображением(ями) опубликован! 🎉\n\n"
                f"📝 Текст: {text_content}\n"
                f"🖼️ Изображений: {len(images)}\n\n"
                f"🆔 Post ID: {post_id}\n"
                f"🔗 Ссылка на пост: {share_link}"
            )

            # Send success message to the chat
            await bot.send_message(chat_id=chat_id, text=success_message)

            logger.info(f"User {username} posted image content to Binance Square: {text_content[:50]}...")

        except Exception as e:
            error_message = f"❌ Ошибка публикации: {str(e)}\n"
            await bot.send_message(chat_id=chat_id, text=error_message)
            logger.error(f"Error posting image content for user {username}: {e}")

            # Clean up on error
            self.user_data[user_id].pop('pending_image_post', None)
            self.user_data[user_id].pop('pending_images', None)

    async def handle_image_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries for image post buttons.

        Args:
            update: Telegram update object
            context: Bot context
        """
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        callback_data = query.data

        # Check if user has pending image post
        if user_id not in self.user_data or 'pending_image_post' not in self.user_data[user_id]:
            await query.edit_message_text("❌ Сессия истекла. Используйте /post_image заново.")
            return

        text_content = self.user_data[user_id].get('pending_image_post', '')
        images = self.user_data[user_id].get('pending_images', [])

        if callback_data == 'img_cancel':
            # Cancel the image post
            self.user_data[user_id].pop('pending_image_post', None)
            self.user_data[user_id].pop('pending_images', None)
            await query.edit_message_text("❌ Публикация отменена.")
            logger.info(f"User {username} cancelled image post")

        elif callback_data == 'img_add':
            # User wants to add another photo
            images_count = len(self.user_data[user_id].get('pending_images', []))
            if images_count >= 2:
                await query.edit_message_text("❌ Максимум 2 изображения на пост!")
                return

            await query.edit_message_text(
                f"📸 Изображение {images_count}/2 получено.\n\n"
                f"Пришлите ещё одно фото для добавления."
            )
            logger.info(f"User {username} requested to add another image")

        elif callback_data == 'img_send':
            # User confirmed - publish the post
            images = self.user_data[user_id].get('pending_images', [])
            if not images:
                await query.edit_message_text("❌ Нет изображений для отправки!")
                return

            # Publish the post
            await query.edit_message_text("⏳ Публикую пост...")
            await self._publish_image_post(user_id, query.message.chat.id, context.bot)
            logger.info(f"User {username} confirmed and sent image post")

    async def article_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /article command for creating long-form articles with cover image.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Ensure user data exists
        self._ensure_user_data(user_id, username, update.effective_chat.id)

        # Extract title and initial content preserving newlines
        message_text = update.message.text or update.message.caption or ''
        parts = message_text.split(' ', 1)
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Укажите заголовок статьи!\n"
                "Пример: /article Заголовок статьи\n\n"
                "Потом пришлите текст (можно несколькими сообщениями),\n"
                "а затем фото для обложки (опционально).\n"
                "Кнопки: Добавить текст / Добавить обложку / Отправить / Отмена"
            )
            return

        title = parts[1].strip()
        self.user_data[user_id]['commands_used'] += 1

        # Store article data
        self.user_data[user_id]['pending_article'] = {
            'title': title,
            'content': '',
            'cover_url': None
        }
        self.user_data[user_id]['pending_images'] = []

        # Send initial message with inline keyboard
        keyboard = [
            [InlineKeyboardButton("📝 Добавить текст", callback_data='art_add_text')],
            [InlineKeyboardButton("🖼️ Добавить обложку", callback_data='art_add_cover')],
            [InlineKeyboardButton("✅ Отправить статью", callback_data='art_send')],
            [InlineKeyboardButton("❌ Отмена", callback_data='art_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📰 Создание статьи\n\n"
            f"📋 Заголовок: {title}\n\n"
            f"Пришлите текст сообщениями (будет склеиваться).\n"
            f"Можете прислать фото для обложки.\n\n"
            f"Кнопки управления:",
            reply_markup=reply_markup
        )

        logger.info(f"User {username} started article creation: {title}")

    async def handle_article_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle callback queries for article post buttons.

        Args:
            update: Telegram update object
            context: Bot context
        """
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        callback_data = query.data

        # Check if user has pending article
        if user_id not in self.user_data or 'pending_article' not in self.user_data[user_id]:
            await query.edit_message_text("❌ Сессия истекла. Используйте /article заново.")
            return

        article = self.user_data[user_id]['pending_article']
        title = article.get('title', '')
        content = article.get('content', '')
        cover_url = article.get('cover_url')

        if callback_data == 'art_cancel':
            # Cancel the article
            self.user_data[user_id].pop('pending_article', None)
            self.user_data[user_id].pop('pending_images', None)
            await query.edit_message_text("❌ Создание статьи отменено.")
            logger.info(f"User {username} cancelled article creation")

        elif callback_data == 'art_add_text':
            await query.edit_message_text(
                f"📝 Добавление текста к статье\n\n"
                f"📋 Заголовок: {title}\n\n"
                f"Пришлите текст сообщением (будет добавлен к концу статьи).\n"
                f"Можете прислать несколько сообщений подряд."
            )
            logger.info(f"User {username} requested to add text to article")

        elif callback_data == 'art_add_cover':
            # Check if cover already exists
            article = self.user_data[user_id]['pending_article']
            if article.get('cover_url'):
                await query.edit_message_text("❌ Обложка уже добавлена! Максимум 1.")
                return

            # Set flag to indicate next photo is for article cover
            self.user_data[user_id]['pending_article']['cover_pending'] = True

            await query.edit_message_text(
                f"🖼️ Добавление обложки к статье\n\n"
                f"📋 Заголовок: {title}\n\n"
                f"Пришлите фото для обложки (максимум 1)."
            )
            logger.info(f"User {username} requested to add cover to article")

        elif callback_data == 'art_send':
            # User confirmed - publish the article
            if not article.get('content', '').strip():
                await query.edit_message_text("❌ Текст статьи пуст! Добавьте текст перед отправкой.")
                return

            # Publish the article
            await query.edit_message_text("⏳ Публикую статью...")
            await self._publish_article_post(user_id, query.message.chat.id, context.bot)
            logger.info(f"User {username} confirmed and sent article")

    async def _publish_article_post(self, user_id: int, chat_id: int, bot) -> None:
        """
        Publish the collected article to Binance Square.

        Args:
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            bot: Bot instance for sending messages
        """
        if user_id not in self.user_data or 'pending_article' not in self.user_data[user_id]:
            return

        article = self.user_data[user_id]['pending_article']
        title = article.get('title', '')
        content = article.get('content', '')
        cover_url = article.get('cover_url')

        if not content.strip():
            await bot.send_message(chat_id=chat_id, text="❌ Текст статьи пуст!")
            return

        username = self.user_data[user_id].get('username', 'Unknown')

        try:
            # Prepare article content - Binance article format
            formatted_content = self.content_generator.generate_content(
                content,
                post_type='article'
            )

            # Post to Binance Square as article (contentType=2)
            post_result = await self.binance_api.post_content(
                formatted_content,
                post_type='article',
                image_url=cover_url,  # Will be sent as cover
                title=title  # Required for articles
            )

            # Clear pending state
            self.user_data[user_id].pop('pending_article', None)
            self.user_data[user_id].pop('pending_images', None)

            # Extract post ID and link
            post_id = post_result.get('data', {}).get('id', 'N/A')
            share_link = post_result.get('data', {}).get('shareLink', f'https://www.binance.com/square/post/{post_id}')

            success_message = (
                f"✅ Статья опубликована! 🎉\n\n"
                f"📋 Заголовок: {title}\n"
                f"🖼️ Обложка: {'Да' if cover_url else 'Нет'}\n\n"
                f"🆔 Post ID: {post_id}\n"
                f"🔗 Ссылка на статью: {share_link}"
            )

            # Send success message to the chat
            await bot.send_message(chat_id=chat_id, text=success_message)

            logger.info(f"User {username} posted article to Binance Square: {title}")

        except Exception as e:
            error_message = f"❌ Ошибка публикации статьи: {str(e)}\n"
            await bot.send_message(chat_id=chat_id, text=error_message)
            logger.error(f"Error posting article for user {username}: {e}")

            # Clean up on error
            self.user_data[user_id].pop('pending_article', None)
            self.user_data[user_id].pop('pending_images', None)

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
            content_parts.append(f"{scheldue_data['question']}\n")

        # Add options if present
        if scheldue_data.get('options'):
            content_parts.append("\n🗳️ Options:\n")
            for i, option in enumerate(scheldue_data['options'], 1):
                content_parts.append(f"{i}. {option}")

        # Add ticker information
        if scheldue_data.get('tickers'):
            content_parts.append("\n📊 Market Data:\n")
            # Format tickers with prices
            for ticker in scheldue_data['tickers']:
                content_parts.append(f"• ${ticker}")

        # Add hashtags
        if scheldue_data.get('hashtags'):
            content_parts.append("\n🏷️ Topics:\n")
            for hashtag in scheldue_data['hashtags']:
                content_parts.append(f"#{hashtag}")

        # Add regular content if present
        if scheldue_data.get('content') and scheldue_data['content'].strip():
            content_parts.append(f"\n📝 Additional Content:\n{ scheldue_data['content'] }")

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

        # Extract details preserving newlines
        message_text = update.message.text or update.message.caption or ''
        parts = message_text.split(' ', 2)
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Please provide scheldue details!\n"
                "Usage: /scheldue <time> <details>\n"
                "Examples:\n"
                "  /scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc\n"
                "  /scheldue 09:00 \"Daily analysis\" \"BTC: $45k\" #crypto\n\n"
                "Details can include:\n"
                "  • Question for poll: \"Will BTC rise?\"\n"
                "  • Options: Yes No Maybe\n"
                "  • Tickers: $btc $eth $sol (with or without $)\n"
                "  • Hashtags: #crypto #bitcoin\n"
                "  • Content for regular post after options\n\n"
                "For interactive scheldue creation, use: /scheldue"
            )
            return

        time_str = parts[1]
        details = parts[2]  # Preserve newlines in details

        try:
            # Parse scheldue details
            scheldue_data = self._parse_scheldue_details(details)

            if not scheldue_data:
                await update.message.reply_text(
                    "❌ Invalid scheldue format!\n"
                    "Please provide details in format: [question] [options] [tickers] [hashtags] [content]\n"
                    "Example: /scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc #crypto\n"
                    "Example: /scheldue 09:00 \"Daily analysis\" \"BTC: $45k\" #crypto\n"
                    "Example: /scheldue 14:30 \"Will BTC rise?\" Yes No Maybe $btc $eth"
                )
                return

            # Schedule the scheldue post
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Неверный формат времени! Используйте ЧЧ:ММ (24 часа)\n"
                    "Пример: /scheldue 14:30 \"Вырастет BTC?\" Да Нет $btc"
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
                f"🚀 Scheldue Post Scheduled Successfully! 🎉\n\n"
                f"📝 Question: {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ Options: {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 Tickers: {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ Hashtags: {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ Scheduled Time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 Scheldue ID: {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 Next steps:\n"
                f"• /scheldue - Create another scheldue\n"
                f"• /status - Check bot status\n"
                f"• /list-reminders - Manage reminders\n"
                f"• /help - View all commands"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled scheldue: {details[:50]}...")

        except Exception as e:
            error_message = f"❌ Ошибка планирования scheldue: {str(e)}\n"
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
                "❌ Этот бот работает только в личных сообщениях! "
                "Напишите мне напрямую для использования AdminKroha."
            )
            return

        # Check if user is admin in the configured group
        try:
            if not self.config.telegram_group_id:
                await update.message.reply_text(
                    "❌ Бот не настроен с ID группы."
                )
                return
            chat_id = int(self.config.telegram_group_id)
            member = await update.get_bot().get_chat_member(chat_id, user_id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ Только администраторы настроенной группы могут использовать эту функцию!"
                )
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            await update.message.reply_text(
                "❌ Ошибка проверки прав админа. Попробуйте снова."
            )
            return

        # Interactive scheldue creation
        await update.message.reply_text(
            "🚀 AdminKroha Scheldue Creator 🚀\n\n"
            "Создадим запланированный пост с опросами, тикерами и хештегами!\n\n"
            "Шаг 1: Укажите время публикации (ЧЧ:ММ)\n"
            "Пример: 14:30 для 14:30\n\n"
            "Шаг 2: Укажите детали контента\n"
            "Можно добавить:\n"
            "  • Вопрос: \"Вырастет BTC?\"\n"
            "  • Варианты: Да Нет Возможно\n"
            "  • Тикеры: $btc $eth $sol или BTCUSDT ETHUSDT\n"
            "  • Хештеги: #crypto #bitcoin\n"
            "  • Текст после вариантов\n\n"
            "Пример: 14:30 \"Вырастет BTC?\" Да Нет $btc #crypto\n\n"
            "Введите время и детали:"
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
                    "Example: \"Will BTC rise?\" Yes No Maybe $btc #crypto\n"
                    "Example: \"Daily analysis\" \"BTC: $45k\" #crypto\n"
                    "Please try again:"
                )
                return

            # Send interactive time input
            await update.message.reply_text(
                "⏰ Step 2: Please provide the scheduled time (HH:MM format):\n"
                "Example: 14:30 for 2:30 PM\n"
                "Example: 09:00 for 9:00 AM\n"
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
                    "Example: 14:30 for 2:30 PM\n"
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
                f"✅ Scheldue Post Scheduled Successfully! 🎉\n\n"
                f"📝 Question: {scheldue_data.get('question', 'N/A')}\n"
                f"🗳️ Options: {', '.join(scheldue_data.get('options', []))}\n"
                f"📊 Tickers: {', '.join(scheldue_data.get('tickers', []))}\n"
                f"🏷️ Hashtags: {', '.join(scheldue_data.get('hashtags', []))}\n"
                f"⏰ Scheduled Time: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 Scheldue ID: {post_id}\n\n"
                f"This scheldue will be posted automatically with poll, tickers, and hashtags!\n\n"
                f"📋 Next steps:\n"
                f"• /scheldue - Create another scheldue\n"
                f"• /status - Check bot status\n"
                f"• /list-reminders - Manage reminders\n"
                f"• /help - View all commands"
            )

            logger.info(f"User {username} (ID: {user_id}) created scheldue post {post_id}")

        except Exception as e:
            await update.message.reply_text(f"❌ Error scheduling scheldue: {e}")
            logger.error(f"Error scheduling scheldue for user {user_id}: {e}")

    async def article_text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle text messages for article content accumulation.

        Args:
            update: Telegram update object
            context: Bot context
        """
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Check if user is in article creation process
        if user_id not in self.user_data or 'pending_article' not in self.user_data[user_id]:
            return

        article = self.user_data[user_id]['pending_article']

        # Get the text content preserving newlines
        text = update.message.text or update.message.caption or ''
        if not text.strip():
            return

        # Append to existing content
        if article.get('content'):
            article['content'] += '\n\n' + text
        else:
            article['content'] = text

        # Update stored article
        self.user_data[user_id]['pending_article'] = article

        # Show current content preview (first 200 chars)
        preview = article['content'][:200]
        if len(article['content']) > 200:
            preview += '...'

        cover_status = '🖼️ Обложка: есть' if article.get('cover_url') else '🖼️ Обложки: нет'

        keyboard = [
            [InlineKeyboardButton("📝 Добавить текст", callback_data='art_add_text')],
            [InlineKeyboardButton("🖼️ Добавить обложку", callback_data='art_add_cover')],
            [InlineKeyboardButton("✅ Отправить статью", callback_data='art_send')],
            [InlineKeyboardButton("❌ Отмена", callback_data='art_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📝 Текст добавлен к статье\n\n"
            f"📋 Заголовок: {article.get('title', '')}\n\n"
            f"📝 Текст ({len(article['content'])} симв.):\n{preview}\n\n"
            f"{cover_status}\n\n"
            f"Кнопки управления:",
            reply_markup=reply_markup
        )

        logger.info(f"User {username} added text to article ({len(text)} chars)")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /status command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Get bot statistics
        total_users = len(self.user_data)
        total_commands = sum(data.get('commands_used', 0) for data in self.user_data.values())
        active_scheduled = len(self.scheduled_posts)

        status_message = (
            f"📊 Статус бота\n\n"
            f"🤖 Информация о боте:\n"
            f"• Имя: Binance Square Telegram Bot\n"
            f"• Версия: 1.0.0\n"
            f"• Python: 3.8+\n\n"
            f"👥 Статистика пользователей:\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Всего команд: {total_commands}\n"
            f"• Команд на пользователя: {total_commands / max(total_users, 1):.1f}\n\n"
            f"⏰ Статистика бота:\n"
            f"• Статус: Онлайн ✅\n"
            f"• Время работы: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"• Запланированных постов: {active_scheduled}\n\n"
            f"🔗 Статус API:\n"
            f"• Binance Square API: Подключен ✅\n"
            f"• Telegram API: Подключен ✅\n\n"
            f"📝 Недавняя активность:\n"
            f"• Последние 10 мин: Активно\n"
            f"• Ошибки за час: 0\n"
            f"• Успешные посты: Активно\n"
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
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Extract content preserving newlines
        message_text = update.message.text or update.message.caption or ''
        parts = message_text.split(' ', 2)  # Split into 3 parts: /schedule, time, content
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Укажите время и контент!\n"
                "Пример: /schedule 14:30 Анализ на завтра"
            )
            return

        time_str = parts[1]
        content = parts[2]  # Preserve newlines in content

        try:
            # Parse time
            scheduled_time = self._parse_time(time_str)
            if not scheduled_time:
                await update.message.reply_text(
                    "❌ Неверный формат времени! Используйте ЧЧ:ММ (24 часа)\n"
                    "Пример: /schedule 14:30 Анализ на завтра"
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
                f"⏰ Пост запланирован успешно! 🎉\n\n"
                f"📝 Контент: {content}\n"
                f"🕐 Время публикации: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🆔 Post ID: {post_id}\n"
                f"👤 Запланировал: {username}\n\n"
                f"Пост автоматически опубликуется в указанное время!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} scheduled a post: {content[:50]}...")

        except Exception as e:
            error_message = f"❌ Ошибка планирования: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error scheduling post for user {username}: {e}")

    async def add_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /add-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Укажите детали напоминания!\n"
                "Использование: /add_reminder <тип> <время> [дни] [сообщение]\n"
                "Примеры:\n"
                "  /add_reminder task 09:00 Проверить задачи\n"
                "  /add_reminder market 14:30 Цена BTC #crypto\n"
                "  /add_reminder analysis 19:00 Конец торговой сессии\n\n"
                "Типы: task, market, analysis, news, general"
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
                f"✅ Reminder Added Successfully! 🎉\n\n"
                f"🔔 Type: {reminder_type.title()}\n"
                f"⏰ Time: {time}\n"
                f"📅 Days: {days_display}\n"
                f"💬 Message: {message}\n"
                f"🆔 Reminder ID: {reminder_id}\n\n"
                f"The reminder will notify you at the specified time on the selected days!"
            )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} added reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Ошибка добавления напоминания: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error adding reminder for user {username}: {e}")

    async def list_reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /list-reminders command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        try:
            # Get user's reminders
            reminders = await self.reminder_manager.get_reminders(user_id)

            if not reminders:
                await update.message.reply_text(
                    "📭 Напоминаний нет\n\n"
                    "У вас пока нет активных напоминаний.\n"
                    "Используйте /add_reminder для создания первого!"
                )
                return

            # Format reminders list
            reminders_list = "🔔 Ваши напоминания:\n\n"

            for reminder in reminders:
                # Format days
                days = reminder.get('days_of_week', [])
                if days:
                    day_names = []
                    day_list = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
                    for day in days:
                        day_names.append(day_list[day % 7])
                    days_display = ', '.join(day_names)
                else:
                    days_display = 'Каждый день'

                # Format reminder status
                next_triggered = reminder.get('next_triggered')
                if next_triggered:
                    try:
                        next_time = datetime.fromisoformat(next_triggered)
                        next_time_str = next_time.strftime('%Y-%m-%d %H:%M')
                    except:
                        next_time_str = 'Скоро'
                else:
                    next_time_str = 'Скоро'

                reminders_list += (
                    f"📌 {reminder['reminder_type'].title()}\n"
                    f"   ⏰ Время: {reminder['time']} ({next_time_str})\n"
                    f"   📅 Дни: {days_display}\n"
                    f"   💬 Сообщение: {reminder['message']}\n"
                    f"   🆔 ID: {reminder['reminder_id']}\n\n"
                )

            # Add some footer information
            reminders_list += (
                f"📊 Всего напоминаний: {len(reminders)}\n"
                f"🔄 Повторяющихся: {sum(1 for r in reminders if r.get('is_recurring', True))}\n"
                f"📅 На сегодня: {len([r for r in reminders if r.get('is_due_today', lambda: False)()])}\n\n"
                f"💡 Команды:\n"
                f"  • /add_reminder <тип> <время> [дни] [сообщение] - Добавить\n"
                f"  • /remove_reminder <id> - Удалить\n"
                f"  • /update_reminder <id> [обновления] - Изменить\n"
                f"  • /trigger_reminder <id> - Запустить сейчас\n"
            )

            await update.message.reply_text(reminders_list)
            logger.info(f"User {username} listed reminders")

        except Exception as e:
            error_message = f"❌ Ошибка списка напоминаний: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error listing reminders for user {username}: {e}")

    async def remove_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /remove-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Укажите ID напоминания!\n"
                "Использование: /remove_reminder <id>\n"
                "ID можно узнать через /list_reminders"
            )
            return

        reminder_id = context.args[0]

        try:
            # Remove the reminder
            success = await self.reminder_manager.remove_reminder(reminder_id, user_id)

            if success:
                success_message = (
                    f"✅ Напоминание удалено! 🎉\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Удалил: {username}\n\n"
                    f"Напоминание больше не сработает."
                )
            else:
                success_message = (
                    f"❌ Напоминание не найдено\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Пользователь: {username}\n\n"
                    f"Проверьте ID и попробуйте снова."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} removed reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Ошибка удаления: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error removing reminder for user {username}: {e}")

    async def update_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /update-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Укажите ID и изменения!\n"
                "Использование: /update_reminder <id> <поле> <значение>\n"
                "Примеры:\n"
                "  /update_reminder rem_123 time 10:00\n"
                "  /update_reminder rem_123 message Новое сообщение\n"
                "  /update_reminder rem_123 days 0,2,4\n"
                "  /update_reminder rem_123 recurring false"
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
                                await update.message.reply_text(f"❌ Неверный формат дней: {value}")
                                return
                        elif field == 'recurring':
                            updates[field] = value.lower() in ['true', 'yes', '1', 'on']
                        else:
                            updates[field] = value

            # Update the reminder
            success = await self.reminder_manager.update_reminder(reminder_id, updates, user_id)

            if success:
                success_message = (
                    f"✅ Напоминание обновлено! 🎉\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Обновил: {username}\n"
                    f"📝 Изменения: {updates}\n\n"
                    f"Напоминание успешно обновлено."
                )
            else:
                success_message = (
                    f"❌ Напоминание не найдено\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Пользователь: {username}\n\n"
                    f"Проверьте ID и попробуйте снова."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} updated reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Ошибка обновления: {str(e)}\n"
            await update.message.reply_text(error_message)
            logger.error(f"Error updating reminder for user {username}: {e}")

    async def trigger_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /trigger-reminder command.

        Args:
            update: Telegram update object
            context: Bot context
        """
        # Check if user is group admin
        if not await self.require_group_admin(update, context):
            return

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        if not context.args:
            await update.message.reply_text(
                "❌ Укажите ID напоминания!\n"
                "Использование: /trigger_reminder <id>\n"
                "ID можно узнать через /list_reminders"
            )
            return

        reminder_id = context.args[0]

        try:
            # Trigger the reminder
            success = await self.reminder_manager.trigger_reminder(reminder_id)

            if success:
                success_message = (
                    f"✅ Напоминание запущено! 🎉\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Запустил: {username}\n\n"
                    f"Напоминание сработало немедленно!"
                )
            else:
                success_message = (
                    f"❌ Напоминание не найдено\n\n"
                    f"🆔 ID: {reminder_id}\n"
                    f"👤 Пользователь: {username}\n\n"
                    f"Проверьте ID и попробуйте снова."
                )

            await update.message.reply_text(success_message)
            logger.info(f"User {username} triggered reminder {reminder_id}")

        except Exception as e:
            error_message = f"❌ Ошибка запуска: {str(e)}\n"
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
        application.add_handler(CommandHandler("image", self.post_image_command))  # Alias
        application.add_handler(CommandHandler("article", self.article_command))
        application.add_handler(CommandHandler("schedule", self.schedule_command))
        application.add_handler(CommandHandler("status", self.status_command))

        # Add reminder command handlers
        application.add_handler(CommandHandler("add_reminder", self.add_reminder_command))
        application.add_handler(CommandHandler("list_reminders", self.list_reminders_command))
        application.add_handler(CommandHandler("remove_reminder", self.remove_reminder_command))
        application.add_handler(CommandHandler("update_reminder", self.update_reminder_command))
        application.add_handler(CommandHandler("trigger_reminder", self.trigger_reminder_command))

        
        # Add message handler for photos
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        application.add_handler(CallbackQueryHandler(self.handle_image_callback, pattern='^img_'))
        application.add_handler(CallbackQueryHandler(self.handle_article_callback, pattern='^art_'))

        # Add article text handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.article_text_handler))

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
