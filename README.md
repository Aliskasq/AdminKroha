# AdminKroha - Enhanced Telegram Bot for Binance Square

## 🚀 Welcome to AdminKroha

**AdminKroha is an advanced Telegram bot for Binance Square with 24/7 operation via systemd, enhanced virtual environment setup, and a comprehensive reminder system.** It builds upon the original Telegram Binance Bot with powerful new features for production deployment.

![Bot Logo](https://github.com/AdminKroha/AdminKroha/blob/main/docs/logo.png?raw=true)

## 📋 Overview

AdminKroha is a next-generation Telegram bot that allows users to post content to Binance Square via Telegram commands. It features:

- **24/7 Production Operation**: Systemd service for continuous uptime
- **Python 3.11+ Virtual Environment**: Enhanced dependency management
- **Advanced Reminder System**: Customizable time and days of week
- **Real-time Market Data**: Cryptocurrency ticker integration
- **Content Scheduling**: Automatic post scheduling with preview
- **Multi-language Support**: Internationalization-ready
- **Advanced Analytics**: Comprehensive bot statistics
- **Security Hardening**: Production-ready security measures

## ✨ Key Features

### 🔔 Advanced Reminder System
- **Customizable Time & Days**: Set reminders for specific times and days
- **Multiple Types**: Task, market, analysis, news, and general reminders
- **Flexible Scheduling**: Repeat daily, weekly, or custom day selections
- **Easy Management**: Add, list, update, and remove reminders
- **Immediate Trigger**: Manually trigger reminders when needed

### 🛠️ Enhanced Virtual Environment
- **Python 3.11+ Support**: Latest Python features and performance
- **Automated Setup**: One-click virtual environment creation
- **Dependency Management**: Automatic requirements installation
- **Production Ready**: Optimized for 24/7 operation

### 📊 24/7 Systemd Operation
- **Automatic Restart**: Systemd manages bot lifecycle
- **Resource Management**: CPU, memory, and file limits
- **Logging Integration**: Journalctl integration for monitoring
- **Security Hardening**: Read-only filesystem, private tmp
- **Health Monitoring**: Automatic status checking

### 📱 Telegram Commands

#### Basic Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot and show help | `/start` |
| `/help` | Show all available commands | `/help` |
| `/status` | Check bot status | `/status` |

#### Content Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/post <text>` | Post text content to Binance Square | `/post BTC price breakout today #crypto #trading` |
| `/post-image <text>` | Post content with image | `/post-image Market analysis` |
| `/get-tickers <tickers>` | Get ticker data | `/get-tickers BTCUSDT ETHUSDT SOLUSDT` |
| `/poll <question> <options>` | Create a poll | `/poll Will BTC go up? Yes No Maybe` |
| `/schedule <time> <text>` | Schedule a post | `/schedule 14:30 Market analysis tomorrow` |

#### Reminder Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/add-reminder <type> <time> [days] [message]` | Add new reminder | `/add-reminder task 09:00 Check daily tasks` |
| `/list-reminders` | List all reminders | `/list-reminders` |
| `/remove-reminder <id>` | Remove a reminder | `/remove-reminder rem_123` |
| `/update-reminder <id> [updates]` | Update a reminder | `/update-reminder rem_123 time 10:00` |
| `/trigger-reminder <id>` | Trigger reminder immediately | `/trigger-reminder rem_123` |

## 🛠️ Installation and Setup

### Prerequisites

- **Python 3.11+** (recommended for enhanced features)
- **Linux system** with systemd (for 24/7 operation)
- **Virtual environment** support (`python3-venv` package)
- **Git** for repository management

### Step 1: Clone the Repository

```bash
# Clone this repository
git clone https://github.com/AdminKroha/AdminKroha.git

# Navigate to the project directory
cd AdminKroha
```

### Step 2: Install Dependencies

**Option A: Use Enhanced Installer (Recommended)**

```bash
# Run the enhanced installer
python3 install.py

# Follow the prompts for:
# • Python 3.11+ virtual environment setup
# • Systemd service configuration
# • Environment variable setup
```

**Option B: Manual Installation**

```bash
# Check Python version
python3 --version

# Create virtual environment (Python 3.11+ recommended)
python3 -m venv venv_production

# Activate virtual environment
# On Linux/macOS:
source venv_production/bin/activate

# On Windows:
venv_production\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create `.env` file from the example:

```bash
# Copy example to .env
cp configs/.env.example .env

# Edit .env with your credentials
# Telegram Bot Token (from @BotFather)
BOT_TOKEN=your_telegram_bot_token_here

# Binance Square API Key
BINANCE_API_KEY=your_binance_square_api_key_here

# Optional: Admin user ID (for admin commands)
ADMIN_USER_ID=your_telegram_user_id

# Optional: Log level
LOG_LEVEL=INFO

# Optional: Maximum post length
MAX_POST_LENGTH=1000

# Optional: Rate limit for API calls
RATE_LIMIT=60
```

### Step 4: Create Directory Structure

```bash
# Create necessary directories
mkdir -p logs data configs systemd docs tests backups cache
```

### Step 5: Configure Systemd Service

```bash
# Copy enhanced systemd service file
sudo cp systemd/admin-kroha.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable admin-kroha
sudo systemctl start admin-kroha

# Check service status
sudo systemctl status admin-kroha
```

## 🚀 Quick Start

### For Development

```bash
# Activate virtual environment
# On Linux/macOS:
source venv_production/bin/activate

# On Windows:
venv_production\Scripts\activate

# Run the bot
python3 main.py
```

### For Production

```bash
# Start with systemd
sudo systemctl start admin-kroha

# Check status
sudo systemctl status admin-kroha

# View logs
sudo journalctl -u admin-kroha -f

# Restart if needed
sudo systemctl restart admin-kroha

# Stop if needed
sudo systemctl stop admin-kroha
```

## 🔔 Reminder System

The AdminKroha bot includes an advanced reminder system with customizable schedules.

### Adding a Reminder

```
/add-reminder <type> <time> [days] [message>
```

**Parameters:**
- `<type>`: Reminder type (task, market, analysis, news, general)
- `<time>`: Time in HH:MM format (24-hour)
- `[days]`: Days to trigger (0=Monday, 6=Sunday, e.g., "0,2,4" for Mon, Wed, Fri)
- `[message]`: Custom reminder message

**Examples:**
```
/add-reminder task 09:00 Check daily tasks
/add-reminder market 14:30 BTC price check #crypto
/add-reminder analysis 19:00 Daily analysis reminder
/add-reminder news 08:00 Morning news briefing
/add-reminder general 17:00 Team standup
```

### Managing Reminders

- `/list-reminders`: View all your reminders
- `/remove-reminder <id>`: Remove a reminder
- `/update-reminder <id> [updates]`: Update a reminder
- `/trigger-reminder <id>`: Trigger immediately

## 📁 Project Structure

```
AdminKroha/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot logic with reminder system
│   ├── binance_api.py      # Binance Square API integration
│   ├── content_generator.py # Content generation and formatting
│   ├── image_handler.py   # Image processing and upload
│   ├── scheduler.py       # Post scheduling
│   ├── logger.py          # Logging configuration
│   └── reminder.py        # Advanced reminder system
├── configs/
│   ├── .env.example       # Environment file example
│   └── ecosystem.config.js # PM2 configuration
├── systemd/
│   └── admin-kroha.service # Enhanced systemd service file
├── logs/                  # Bot logs (auto-managed)
├── data/                  # Data storage
├── docs/                  # Documentation
├── tests/                 # Tests
├── backups/               # Backup files
├── cache/                 # Cache files
├── install.py            # Enhanced installation script
├── main.py                # Entry point
├── README.md              # This documentation
└── requirements.txt       # Python dependencies
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token | Yes |
| `BINANCE_API_KEY` | Binance Square API Key | Yes |
| `ADMIN_USER_ID` | Admin user ID | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `MAX_POST_LENGTH` | Maximum post length | No |
| `RATE_LIMIT` | Rate limit for API calls | No |

### Bot Configuration

Edit `src/config.py` to adjust bot behavior:

```python
class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_POST_LENGTH = int(os.getenv('MAX_POST_LENGTH', '1000'))
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '60'))
```

## 📊 API Integration

### Binance Square API

The bot uses the Binance Square API to post content:

#### Endpoints

- **Post Content**: `POST https://api.binance.com/square/api/v1/content`
- **Upload Image**: `POST https://api.binance.com/square/api/v1/image`
- **Get Tickers**: `GET https://api.binance.com/api/v3/ticker/24hr`

#### API Key Setup

1. Get a Binance Square API key from the Binance Square platform
2. Ensure the key has necessary permissions
3. Store the key securely in the `.env` file

### Telegram API

The bot uses the Telegram Bot API:

#### Bot Creation

1. Start a chat with [@BotFather](https://t.me/BotFather)
2. Use `/newbot` to create a new bot
3. Follow the instructions to get your bot token
4. Set up webhook or use polling (polling recommended for this bot)

## 👥 Bot Commands

### Basic Commands

- `/start` - Start the bot and show help
- `/help` - Show all available commands

### Content Commands

- `/post <text>` - Post text content
- `/post-image <text>` - Post content with image
- `/get-tickers <tickers>` - Get ticker data
- `/poll <question> <option1> <option2> ...` - Create a poll
- `/schedule <time> <text>` - Schedule a post

### Admin Commands

- `/status` - Check bot status and statistics
- `/broadcast <text>` - Send broadcast message (admin only)
- `/logs` - View recent logs (admin only)

### Reminder Commands

- `/add-reminder <type> <time> [days] [message>` - Add new reminder
- `/list-reminders` - List all reminders
- `/remove-reminder <id>` - Remove a reminder
- `/update-reminder <id> [updates]` - Update a reminder
- `/trigger-reminder <id>` - Trigger immediately

## 📈 Usage Examples

### Posting to Binance Square

```bash
# Simple text post
/bot post BTC price breakout today #crypto #trading

# Post with ticker data
/bot post BTC: $45,000 (+2.5%) ETH: $2,300 (+1.2%) #crypto

# Post with hashtags
/bot post Daily market analysis #bitcoin #ethereum #crypto
```

### Getting Ticker Data

```bash
/bot get-tickers BTCUSDT ETHUSDT SOLUSDT

# Output:
BTCUSDT: $45,000 (+2.5%) | High: $46,000 | Low: $44,000
ETHUSDT: $2,300 (+1.2%) | High: $2,350 | Low: $2,250
SOLUSDT: $95 (+3.8%) | High: $100 | Low: $92
```

### Creating a Poll

```bash
/bot poll Will BTC go above $50k next week? Yes No Maybe

# Output: Poll created with options:
# 1. Yes
# 2. No
# 3. Maybe
```

### Using Reminders

```bash
# Add a daily task reminder
/add-reminder task 09:00 Check daily tasks for tomorrow

# Add a market update reminder for specific days
/add-reminder market 14:30 BTC price check #crypto 0,2,4

# View all reminders
/list-reminders
```

## 🐛 Troubleshooting

### Common Issues

#### Bot Not Responding

1. **Check if bot is running**
   ```bash
   sudo systemctl status admin-kroha
   ```

2. **Check logs for errors**
   ```bash
   sudo journalctl -u admin-kroha --since "1 hour ago"
   ```

3. **Restart the bot**
   ```bash
   sudo systemctl restart admin-kroha
   ```

#### Invalid API Keys

1. **Verify Telegram Bot Token**
   - Go to [@BotFather](https://t.me/BotFather)
   - Check if the token is correct

2. **Verify Binance API Key**
   - Go to Binance Square platform
   - Check if the API key is valid and has permissions

#### Permission Errors

1. **Check if bot is added to the chat**
   - Add the bot to your Telegram chat

2. **Check admin permissions**
   - Ensure the bot has necessary permissions in the chat

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run the bot with debug
python3 main.py
```

## 📚 Documentation

### Bot API

See `docs/` for detailed API documentation.

### Configuration

See `src/config.py` for configuration options.

### Development

See `CONTRIBUTING.md` for development guidelines.

## 🆘 Support

### Issues

Report issues at: https://github.com/AdminKroha/AdminKroha/issues

### Discussions

Join the discussion at: https://github.com/AdminKroha/AdminKroha/discussions

### Contact

For direct support, contact the maintainer at:
- GitHub: @AdminKroha
- Email: [contact information]

## 📖 License

This project is licensed under the MIT License. See `LICENSE` for more information.

## 🌟 Credits

- **Binance Square API**: For providing social posting capabilities
- **Telegram Bot API**: For providing messaging platform
- **Python Community**: For providing the Python ecosystem
- **Open Source Contributors**: For their contributions

## 🚀 Future Development

### Planned Features

1. **Enhanced Analytics**: More detailed market analytics
2. **Multi-language Support**: Support for multiple languages
3. **Advanced Scheduling**: Smart scheduling based on market conditions
4. **Real-time Data**: Live data streaming for prices
5. **Web Interface**: Admin web interface for bot management
6. **Mobile App**: Mobile app for bot control

### Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for guidelines.

## 🔄 Changelog

### Version 2.0.0 (Current Release)
- Complete systemd integration for 24/7 operation
- Enhanced virtual environment with Python 3.11+ support
- Advanced reminder system with customizable schedules
- Improved security hardening
- Enhanced documentation
- Updated installation script

### Version 1.0.0 (Initial Release)
- Initial release with core functionality
- Basic content posting
- Ticker data integration
- Simple polling system
- Admin controls

## 📧 Contact

If you have any questions, suggestions, or need help, please:
1. Create an issue on GitHub
2. Start a discussion
3. Contact the maintainer directly

Thank you for using AdminKroha! 🌟

---
*This enhanced bot is designed and maintained by AdminKroha* 🌟
*GitHub: https://github.com/AdminKroha* 📍
*Version: 2.0.0* 📅