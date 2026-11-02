# AdminKroha - Enhanced Telegram Bot for Binance Square

## Project Overview
AdminKroha is an advanced Telegram bot for posting content to Binance Square. It features 24/7 operation via systemd, enhanced virtual environment setup, and a comprehensive reminder system.

**Repository:** https://github.com/Aliskasq/AdminKroha.git
**Current directory:** /home/user/AdminKroha
**Current version:** v2.1.4

## Key Configuration

### Environment Variables (.env)
```bash
BOT_TOKEN=your_bot_token_here          # Get from @BotFather
TELEGRAM_GROUP_ID=-100xxxxxxxxxx       # Your group ID (format: -100...)
BINANCE_API_KEY=your_binance_api_key   # From Binance Square Creator Center
ADMIN_USER_ID=123456789                # Your Telegram user ID (optional)
LOG_LEVEL=INFO
MAX_POST_LENGTH=1000
RATE_LIMIT=60
ENABLE_SCHEDULED_POSTS=true
ENABLE_AUTO_REPLIES=true
ALLOWED_HASHTAGS=#crypto,#btc,#eth,#trading,#binance,#square
DEFAULT_POST_TYPE=text
MAX_MEMORY_USAGE=512
MAX_CONCURRENT_REQUESTS=10
ENABLE_CSRF_PROTECTION=true
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production
DEBUG=false
LOG_FILE=bot.log
MAX_LOG_SIZE=10485760
BACKUP_LOG_COUNT=5
```

> ⚠️ **NEVER commit real credentials to GitHub!** Use `.env` file (gitignored) for actual values.

### Required Dependencies
- Python 3.11+ (tested on 3.14.4, but target VPS uses 3.11)
- python-telegram-bot>=20.7
- aiohttp>=3.14.5
- APScheduler>=3.10.0
- python-dotenv>=1.0.0
- pandas, numpy, pydantic
- loguru, psutil, Pillow
- redis, SQLAlchemy
- httpx, requests

## Project Structure
```
AdminKroha/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration management (dataclass Config)
│   ├── bot.py              # Main bot logic with reminder system (RUSSIAN)
│   ├── binance_api.py      # Binance Square OpenAPI v1/v2 integration
│   ├── content_generator.py # Content generation & formatting (preserves user content)
│   ├── image_handler.py    # Image processing & upload
│   ├── scheduler.py        # Post scheduling
│   ├── logger.py           # Logging configuration
│   └── reminder.py         # Advanced reminder system
├── configs/
│   └── .env.example        # Environment template
├── systemd/
│   └── admin-kroha.service # Systemd service file (NOT modified)
├── logs/                   # Bot logs (auto-managed)
├── data/                   # Data storage
├── install.py              # Enhanced installation script
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
└── README.md               # Documentation (RUSSIAN)
```

## Bot Commands (все на русском)

### Basic
- `/start` - Запуск бота и справка (только группа, только админы)
- `/help` - Показать все команды
- `/status` - Статус бота и статистика

### Content
- `/post <текст>` - Опубликовать текст в Binance Square
- `/post_image <текст>` - Опубликовать с изображением (потом пришлите фото)
- `/schedule <время> <текст>` - Запланировать пост
- `/scheldue <время> <детали>` - Расширенное планирование с тикерами/хештегами

### Reminders
- `/add_reminder <тип> <время> [дни] [сообщение]` - Добавить напоминание
  - Типы: task, market, analysis, news, general
  - Время: ЧЧ:ММ (24ч)
  - Дни: 0=Пн...6=Вс (например "0,2,4" = Пн/Ср/Пт)
- `/list_reminders` - Список напоминаний
- `/remove_reminder <id>` - Удалить напоминание
- `/update_reminder <id> <поле> <значение>` - Обновить напоминание
- `/trigger_reminder <id>` - Запустить немедленно

### Removed Commands (Unsupported by Binance Square)
- `/poll` — Binance Square OpenAPI does not support polls
- `/get_tickers` — Removed (API issues, not core feature)

## Running the Bot

### Development
```bash
cd /home/user/AdminKroha
export PATH="/home/user/.local/bin:$PATH"
python3 main.py
```

### Production (systemd on VPS with Python 3.11)
```bash
# 1. Copy service file
sudo cp systemd/admin-kroha.service /etc/systemd/system/

# 2. Update service file paths for VPS
# Edit /etc/systemd/system/admin-kroha.service to point to VPS paths

# 3. Reload and start
sudo systemctl daemon-reload
sudo systemctl enable admin-kroha
sudo systemctl start admin-kroha

# 4. Monitor
sudo systemctl status admin-kroha
sudo journalctl -u admin-kroha -f
```

### Service File Paths to Update for VPS
In `/etc/systemd/system/admin-kroha.service`:
- `WorkingDirectory=/path/to/AdminKroha`
- `ExecStart=/path/to/venv_production/bin/python main.py`
- `User=your_vps_user`

## Key Fixes Applied (v2.1.4)

1. **Created missing `src/config.py`** - Dataclass Config with load_from_env()
2. **Fixed field order in Config** - Required fields first
3. **Fixed Config() calls without args** in content_generator.py and image_handler.py
4. **Installed missing `aiohttp`** dependency
5. **Fixed .env parsing** - Removed inline comment from MAX_LOG_SIZE
6. **FULL RUSSIAN TRANSLATION** - All 15+ commands messages in Russian
7. **POST LINKS** - Bot returns link after publishing via shareLink API
8. **GROUP ADMIN SUPPORT** - All commands check admin via Telegram API (not hardcoded ADMIN_USER_ID)
   - Added `is_group_admin()` - checks via getChatMember
   - Added `require_group_admin()` - unified check for all commands
   - Any group admin can use bot (not just hardcoded user)
9. **FIXED BINANCE SQUARE API ENDPOINTS** - Now uses correct OpenAPI v1/v2:
   - Text posts: `POST https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add`
   - Image upload: 4-step flow via v2 endpoints (presigned URL → PUT → poll → post)
   - Required headers: `X-Square-OpenAPI-Key`, `clienttype: binanceSkill`
   - Request format: `contentType=1`, `bodyTextOnly` (not `content`/`postType`)
10. **FIXED CONTENT FORMATTING** - Preserves user content exactly per Binance guidelines:
    - No auto hashtags, no timestamps, no "Tags:" prefix
    - Hashtags (#topic) and cashtags ($coin) passed verbatim for backend parsing
11. **REMOVED MARKDOWN FORMATTING** - All bot responses are plain text (no **bold**, no `code`)
12. **REMOVED UNSUPPORTED COMMANDS** - `/poll` and `/get_tickers` removed (Binance Square doesn't support)

## Important Notes

### Security
- Bot **only works in group/supergroup chats** (not private messages)
- **Only group administrators** can use the bot (checked via Telegram API)
- Bot must be added to the target Telegram group AND made admin

### VPS Deployment (Python 3.11)
```bash
# On VPS with Python 3.11:
python3.11 -m venv venv_production
source venv_production/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Copy .env with production keys
# Setup systemd service
```

### Testing Commands
```bash
# Quick test
timeout 15 python3 main.py

# Check config loading
python3 -c "from src.config import Config; c=Config.load_from_env(); print(c.bot_token[:10])"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Config missing args | Ensure .env has BOT_TOKEN, TELEGRAM_GROUP_ID, BINANCE_API_KEY |
| ModuleNotFoundError | Install missing deps: `pip install -r requirements.txt` |
| Bot not responding | Check if added to group, verify TELEGRAM_GROUP_ID format (-100...) |
| Permission denied | Run with correct user, check systemd service User= |
| Python version | Use python3.11 on VPS, ensure venv uses correct python |
| Binance API 403 | Use correct endpoints (www.binance.com/bapi/composite), add clienttype header |

## API Endpoints Used
- Binance Square OpenAPI v1: `POST https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add`
- Binance Square OpenAPI v2 (images):
  - `POST https://www.binance.com/bapi/composite/v2/public/pgc/openApi/image/presignedUrl`
  - `PUT` to presigned URL
  - `POST https://www.binance.com/bapi/composite/v2/public/pgc/openApi/image/imageStatus`
- Binance Public: `GET https://api.binance.com/api/v3/ticker/24hr`
- Telegram Bot API: Long polling via python-telegram-bot

## Development Notes
- Log level: INFO (change to DEBUG for troubleshooting)
- Log rotation: 10MB max, 5 backups
- Rate limit: 60 requests/minute
- Max concurrent requests: 10
- Post length limit: 1000 chars (Telegram max 4096)
- Post link format: shareLink from API (https://app.binance.com/uni-qr/cpos/{id})
- **Content preservation**: User text sent exactly as-is, Binance backend parses #hashtags and $cashtags
- **Plain text only**: No markdown formatting in any bot responses