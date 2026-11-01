#!/usr/bin/env python3
"""
Installation and setup script for Telegram Binance Bot.

This script helps users set up the bot quickly and correctly.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header():
    """Print installation header."""
    print("=" * 60)
    print("AdminKroha Telegram Bot Installer")
    print("=" * 60)
    print()
    print("🚀 Welcome to AdminKroha - Enhanced Telegram Bot for Binance Square")
    print("   with 24/7 operation via systemd and advanced reminder system")
    print()


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    # Check for Python 3.11+ for enhanced features
    if version.major == 3 and version.minor >= 11:
        print("✅ Python 3.11+ detected - Excellent for production deployment!")
    elif version.major == 3 and version.minor >= 8:
        print("✅ Python 3.8+ detected - Compatible with all features")
    else:
        print("❌ ERROR: Python 3.8 or higher is required!")
        return False

    return True


def check_venv():
    """Check if virtual environment is available."""
    print("\nChecking virtual environment...")
    system = platform.system()

    if system == "Windows":
        print("⚠️  Warning: Virtual environment may not be available on Windows")
        print("    Please install Python 3.8+ with pip and venv support")
    else:
        try:
            result = subprocess.run(
                ["python3", "-m", "venv", "--help"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Virtual environment module is available")
                return True
        except Exception:
            pass

        print("⚠️  Warning: Virtual environment may not be available")
        print("    Continuing without virtual environment...")

    return True


def create_virtual_env():
    """Create virtual environment."""
    print("\nCreating Python 3.11+ virtual environment...")
    try:
        # Try to create venv with python3.11 first
        try:
            subprocess.run(["python3.11", "-m", "venv", "venv_production"], check=True)
            venv_path = "venv_production"
            print("✅ Python 3.11 virtual environment created successfully")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fall back to python3
            subprocess.run(["python3", "-m", "venv", "venv"], check=True)
            venv_path = "venv"
            print("⚠️  Warning: Using Python 3 with enhanced venv setup")

        # Create requirements file if needed
        if not os.path.exists("requirements.txt"):
            print("⚠️  Warning: requirements.txt not found, creating basic requirements...")
            with open("requirements.txt", "w") as f:
                f.write("# AdminKroha requirements\n")
                f.write("python-telegram-bot>=20.7\n")
                f.write("requests>=2.31.0\n")
                f.write("python-dotenv>=1.0.0\n")
                f.write("pyyaml>=6.0\n")
                f.write("APScheduler>=3.10.0\n")
                f.write("loguru>=0.7.0\n")
                f.write("redis>=4.6.0\n")
                f.write("SQLAlchemy>=2.0.0\n")
                f.write("Pillow>=10.0.0\n")
                f.write("psutil>=5.9.0\n")

        # Install dependencies in virtual environment
        if venv_path == "venv_production":
            pip_path = f"{venv_path}/bin/pip"
        else:
            if platform.system() != "Windows":
                pip_path = f"{venv_path}/bin/pip3"
            else:
                pip_path = f"{venv_path}\\Scripts\\pip.exe"

        print(f"Installing dependencies in {venv_path}...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")

        # Activate virtual environment
        if platform.system() != "Windows":
            activate_script = f"source {venv_path}/bin/activate"
        else:
            activate_script = f"{venv_path}\\Scripts\\activate.bat"

        print(f"\nTo activate the virtual environment, run: {activate_script}")
        print(f"Your environment is ready: {os.path.abspath(venv_path)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to create virtual environment: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("\nInstalling dependencies...")
    try:
        # Check if requirements.txt exists
        if not os.path.exists("requirements.txt"):
            print("❌ ERROR: requirements.txt not found!")
            return False

        # Install dependencies
        if platform.system() != "Windows":
            subprocess.run(["pip3", "install", "-r", "requirements.txt"], check=True)
        else:
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)

        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file from example."""
    print("\nCreating .env file...")
    try:
        if os.path.exists(".env.example"):
            if os.path.exists(".env"):
                print("⚠️  Warning: .env file already exists")
                print("    Make sure it contains your API keys")
            else:
                # Copy .env.example to .env
                subprocess.run(["cp", ".env.example", ".env"], check=True)
                print("✅ .env file created from .env.example")
                print("    Please edit .env with your API keys")
        else:
            print("❌ ERROR: .env.example not found!")
            return False

        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to create .env file: {e}")
        return False


def create_directory_structure():
    """Create necessary directory structure."""
    print("\nCreating directory structure...")
    directories = [
        "logs",
        "data",
        "configs",
        "systemd",
        "docs",
        "tests",
        "backups",
        "cache"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True


def setup_systemd_service():
    """Setup systemd service file (if on Linux)."""
    print("\nSetting up AdminKroha systemd service...")
    system = platform.system()

    if system != "Linux":
        print("⚠️  Warning: Systemd is only available on Linux")
        print("    Skipping systemd service setup")
        return True

    try:
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        os.makedirs("backups", exist_ok=True)

        # Copy enhanced AdminKroha systemd service file
        subprocess.run(
            ["sudo", "cp", "systemd/admin-kroha.service", "/etc/systemd/system/"],
            check=True
        )
        print("✅ Enhanced AdminKroha systemd service file copied")

        # Reload systemd
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        print("✅ Systemd daemon reloaded")

        # Enable and start service
        subprocess.run(
            ["sudo", "systemctl", "enable", "admin-kroha"],
            check=True
        )
        print("✅ AdminKroha systemd service enabled")

        # Start the service
        subprocess.run(
            ["sudo", "systemctl", "start", "admin-kroha"],
            check=True
        )
        print("✅ AdminKroha service started")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to setup systemd service: {e}")
        return False


def setup_pm2():
    """Setup PM2 process manager (if on Linux/Unix)."""
    print("\nSetting up PM2 process manager...")
    system = platform.system()

    if system != "Linux":
        print("⚠️  Warning: PM2 is only available on Linux/Unix")
        print("    Skipping PM2 setup")
        return True

    try:
        # Check if PM2 is installed
        result = subprocess.run(
            ["which", "pm2"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("⚠️  Warning: PM2 not found, installing...")
            subprocess.run(["npm", "install", "-g", "pm2"], check=True)
            print("✅ PM2 installed")

        # Start bot with PM2
        subprocess.run(
            ["pm2", "start", "ecosystem.config.js", "--name", "telegram-binance-bot"],
            check=True
        )
        print("✅ Bot started with PM2")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to setup PM2: {e}")
        return False


def print_final_instructions():
    """Print final installation instructions."""
    print("\n" + "=" * 60)
    print("ADMINKROHA INSTALLATION COMPLETE! 🚀")
    print("=" * 60)
    print()

    print("🎉 Your AdminKroha bot is now ready for production!")
    print()

    print("📋 Next Steps:")
    print("1. Configure environment variables in .env file")
    print("2. Activate virtual environment (if created)")
    print("3. Test the bot:")
    print("   - For development: python3 main.py")
    print("   - For production (systemd): sudo systemctl status admin-kroha")
    print("4. Monitor logs: sudo journalctl -u admin-kroha -f")
    print("5. Test reminder system: /start to get started")
    print()

    print("🛠️  Useful Commands:")
    print("• Start bot: python3 main.py")
    print("• Stop bot: sudo systemctl stop admin-kroha")
    print("• Restart bot: sudo systemctl restart admin-kroha")
    print("• Check status: sudo systemctl status admin-kroha")
    print("• View logs: sudo journalctl -u admin-kroha -f")
    print("• Enable auto-start: sudo systemctl enable admin-kroha")
    print()

    print("🔔 Reminder System Commands:")
    print("• /add-reminder <type> <time> [days] [message] - Add new reminder")
    print("  Examples:")
    print("    • /add-reminder task 09:00 Check daily tasks")
    print("    • /add-reminder market 14:30 BTC price check #crypto")
    print("    • /add-reminder analysis 19:00 Daily analysis reminder")
    print("• /list-reminders - List all your reminders")
    print("• /remove-reminder <id> - Remove a reminder")
    print("• /update-reminder <id> [updates] - Update a reminder")
    print("• /trigger-reminder <id> - Trigger reminder immediately")
    print()

    print("📁 Project Structure:")
    print("• src/ - Bot source code (includes reminder system)")
    print("• systemd/ - Systemd service files")
    print("• logs/ - Bot logs (auto-managed by systemd)")
    print("• data/ - Data storage")
    print("• backups/ - Backup files")
    print("• configs/ - Configuration files")
    print("• docs/ - Documentation")
    print()

    print("🔧 Configuration:")
    print("• Edit configs/.env.example to create .env with API keys")
    print("• Customize bot settings in src/config.py")
    print("• Configure systemd service in systemd/admin-kroha.service")
    print("• Check logs in logs/ directory")
    print()

    print("📚 Documentation:")
    print("• README.md - Complete user documentation")
    print("• docs/ - Advanced usage and API documentation")
    print("• systemd/ - Systemd service documentation")
    print("• src/reminder.py - Reminder system documentation")
    print()

    print("🛡️  Production Features:")
    print("• 24/7 operation via systemd")
    print("• Python 3.11+ virtual environment")
    print("• Advanced reminder system with customizable schedules")
    print("• Automatic logging and monitoring")
    print("• Security hardening (read-only system, private tmp)")
    print("• Resource limits and restart policies")
    print()

    print("❓ Support:")
    print("• Issues: Check README.md for troubleshooting")
    print("• GitHub: https://github.com/AdminKroha/AdminKroha")
    print("• Documentation: README.md")
    print()

    print("🎯 Next Generation Features Available:")
    print("• Multi-language support")
    print("• Advanced analytics")
    print("• Real-time data streaming")
    print("• Web interface for admin controls")
    print("• Mobile app integration")
    print()


def main():
    """Main installation function."""
    print_header()

    # Check Python version
    if not check_python_version():
        return 1

    # Check virtual environment
    check_venv()

    # Create virtual environment (recommended)
    print("\n🏗️  Setting up virtual environment...")
    if create_virtual_env():
        print("✅ Virtual environment created successfully")
    else:
        print("❌ Failed to create virtual environment, continuing without...")

    # Install dependencies
    if not install_dependencies():
        return 1

    # Create .env file
    create_env_file()

    # Create directory structure
    create_directory_structure()

    # Setup enhanced systemd service (recommended for production)
    print("\n🔄 Setting up systemd service for 24/7 operation...")
    if setup_systemd_service():
        print("✅ Systemd service configured and started")
    else:
        print("⚠️  Systemd setup failed, you may need to install it manually")

    # Print final instructions
    print_final_instructions()

    print("✅ Installation completed successfully!")
    print()
    print("🚀 Your AdminKroha bot is ready for production deployment!")
    print("   Start it with: sudo systemctl start admin-kroha")
    print("   Monitor it with: sudo journalctl -u admin-kroha -f")
    print()


if __name__ == "__main__":
    sys.exit(main())