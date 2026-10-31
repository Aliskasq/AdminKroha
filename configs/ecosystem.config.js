// PM2 Configuration for Telegram Binance Bot

module.exports = {
  apps: [
    {
      name: 'telegram-binance-bot',
      script: 'src/bot.py',
      instances: 'max',
      exec_mode: 'cluster',
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error: './logs/err.log',
      out: './logs/out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      wait_ready: true,
      max_memory_restart: '1G',
      cwd: process.cwd(),
    }
  ]
};