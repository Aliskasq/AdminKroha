# Telegram Bot for Binance Square

## Overview

This repository contains a Python Telegram bot that allows users to post content to Binance Square (Binance's social platform) via Telegram commands. The bot supports posting various types of content including:

- Text posts with hashtags
- Posts with images
- Market analysis with cryptocurrency tickers
- Interactive polls
- Scheduled posts

## Features

### 📱 Telegram Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start the bot and show help | `/start` |
| `/help` | Show all available commands | `/help` |
| `/post <text>` | Post text content to Binance Square | `/post BTC price is up today #crypto #trading` |
| `/post-image <text>` | Post content with image | `/post-image Market analysis` |
| `/get-tickers <tickers>` | Get cryptocurrency ticker data | `/get-tickers BTCUSDT ETHUSDT` |
| `/poll <question> <option1> <option2> <option3>` | Create a poll | `/poll Will BTC go up? Yes No Maybe` |
| `/schedule <time> <text>` | Schedule a post | `/schedule 14:30 Market analysis tomorrow` |
| `/status` | Check bot status | `/status` |

### 📊 Binance Square Integration

- **Auto-posting**: Automatically post content to Binance Square
- **Hashtag support**: Full support for hashtags in posts
- **Image handling**: Upload and post images with content
- **Ticker integration**: Fetch and display real-time cryptocurrency data
- **Error handling**: Robust error handling and retry logic

### 🔧 Admin Controls

- **Status monitoring**: Check bot status and health
- **Log management**: View and manage bot logs
- **Configuration**: Adjust bot settings
- **Updates**: Automated update management

## 🛠️ Installation and Setup

### Requirements

- **Python 3.8+**
- **Telegram Bot Token**: Get from [@BotFather](https://t.me/BotFather)
- **Binance Square API Key**: Get from Binance Square platform
- **VPS or Server** (for 24/7 operation)

### Step 1: Clone the Repository

```bash
# Clone this repository
git clone https://github.com/AdminKroha/telegram-binance-bot.git

# Navigate to the project directory
cd telegram-binance-bot
```

### Step 2: Install Dependencies

```bash
# Option 1: Use install.py script (recommended)
python3 install.py

# Option 2: Manual installation
pip3 install -r requirements.txt
```

### Step 3: Configure the Bot

Create a `.env` file in the project directory:

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
```

### Step 4: Create Necessary Directories

```bash
mkdir -p logs data configs systemd docs tests backups cache
```

### Step 5: Run the Bot

```bash
# Method 1: Using PM2 (recommended for production)
pm2 start ecosystem.config.js --name telegram-binance-bot

# Method 2: Direct execution
python3 main.py

# Method 3: Using systemd (Linux)
sudo systemctl start telegram-binance-bot
sudo systemctl enable telegram-binance-bot
```

### Step 6: Testing

```bash
# Test the bot
curl -X POST https://api.telegram.org/bot<BOT_TOKEN>/sendMessage \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<YOUR_CHAT_ID>", "text": "/start"}'
```

## 🚀 Quick Start

### For Development

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the bot
python3 main.py
```

### For Production

```bash
# Install dependencies
pip3 install -r requirements.txt

# Setup PM2
pm2 start ecosystem.config.js --name telegram-binance-bot

# Setup systemd (optional)
sudo cp systemd/telegram-binance-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-binance-bot
sudo systemctl start telegram-binance-bot
```

## 📁 Project Structure

```
telegram-binance-bot/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot logic
│   ├── binance_api.py      # Binance Square API integration
│   ├── content_generator.py # Content generation and formatting
│   ├── image_handler.py   # Image processing and upload
│   ├── scheduler.py       # Post scheduling
│   └── logger.py          # Logging configuration
├── configs/
│   ├── .env.example       # Environment file example
│   └── ecosystem.config.js # PM2 configuration
├── systemd/
│   └── telegram-binance-bot.service # Systemd service file
├── logs/                  # Bot logs
├── data/                  # Data storage
├── docs/                  # Documentation
├── tests/                 # Tests
├── backups/               # Backup files
├── cache/                 # Cache files
├── install.py            # Installation script
├── main.py                # Entry point
├── README.md              # This file
├── requirements.txt       # Python dependencies
└── ecosystem.config.js    # PM2 configuration
```

## 🔧 Bot Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token | Yes |
| `BINANCE_API_KEY` | Binance Square API Key | Yes |
| `ADMIN_USER_ID` | Admin user ID | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |
| `MAX_POST_LENGTH` | Maximum post length | No |
| `RATE_LIMIT` | Rate limit for API calls | No |

### Configuration Options

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

- `/status` - Check bot status
- `/logs` - View recent logs
- `/broadcast <text>` - Send broadcast message (admin only)

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

## 🐛 Troubleshooting

### Common Issues

#### Bot Not Responding

1. **Check if bot is running**
   ```bash
   pm2 logs telegram-binance-bot
   ```

2. **Check logs for errors**
   ```bash
   pm2 monit
   ```

3. **Restart the bot**
   ```bash
   pm2 restart telegram-binance-bot
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

Report issues at: https://github.com/AdminKroha/telegram-binance-bot/issues

### Discussions

Join the discussion at: https://github.com/AdminKroha/telegram-binance-bot/discussions

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

### Version 1.0.0 (Initial Release)
- Initial release with core functionality
- Basic content posting
- Ticker data integration
- Simple polling system
- Admin controls

### Version 1.1.0 (Upcoming)
- Image upload support
- Advanced scheduling
- Enhanced analytics
- Multi-language support

## 📧 Contact

If you have any questions, suggestions, or need help, please:
1. Create an issue on GitHub
2. Start a discussion
3. Contact the maintainer directly

Thank you for using the Telegram Bot for Binance Square! 🚀

---
*This bot is designed and maintained by AdminKroha* 🌟
*GitHub: https://github.com/AdminKroha* 📍
*Version: 1.0.0* 📅