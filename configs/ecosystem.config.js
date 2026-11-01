// PM2 Configuration for AdminKroha Telegram Bot

module.exports = {
  apps: [
    {
      name: 'admin-kroha',
      script: 'main.py',
      instances: 'max',
      exec_mode: 'cluster',
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8',
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
      // Use virtual environment
      interpreter: './venv_production/bin/python3',
      // Port for log tailing
      port: 9000,
      // PM2 dashboard
      vizion: true,
      // Maximum number of restarts
      max_restarts: 10,
      // Minimum uptime before considering crash
      min_uptime: '10s',
      // Wait for app to be ready
      wait_ready: true,
      // Restart when memory exceeds this limit
      max_memory_restart: '1G',
      // Working directory
      cwd: process.cwd(),
      // Number of instances
      instances: 'max',
      // Cluster mode
      exec_mode: 'cluster',
      // File watching
      watch: false,
      // Log rotation
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    }
  ]
};