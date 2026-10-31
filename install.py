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
    print("Telegram Binance Bot Installer")
    print("=" * 60)
    print()


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8 or higher is required!")
        return False

    print("✅ Python version is acceptable")
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
    print("\nCreating virtual environment...")
    try:
        subprocess.run(["python3", "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")

        # Activate virtual environment
        if platform.system() != "Windows":
            activate_script = "source venv/bin/activate"
        else:
            activate_script = "venv\\Scripts\\activate.bat"

        print(f"To activate the virtual environment, run: {activate_script}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Failed to create virtual environment: {e}")
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
    print("\nSetting up systemd service...")
    system = platform.system()

    if system != "Linux":
        print("⚠️  Warning: Systemd is only available on Linux")
        print("    Skipping systemd service setup")
        return True

    try:
        # Copy systemd service file
        subprocess.run(
            ["sudo", "cp", "systemd/telegram-binance-bot.service", "/etc/systemd/system/"],
            check=True
        )
        print("✅ Systemd service file copied to /etc/systemd/system/")

        # Reload systemd
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        print("✅ Systemd daemon reloaded")

        # Enable and start service
        subprocess.run(
            ["sudo", "systemctl", "enable", "telegram-binance-bot"],
            check=True
        )
        print("✅ Systemd service enabled")

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
    print("INSTALLATION COMPLETE!")
    print("=" * 60)
    print()

    print("Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Activate virtual environment (if created)")
    print("3. Run the bot:")
    print("   - For development: python main.py")
    print("   - For production: pm2 start ecosystem.config.js")
    print("4. Check logs: tail -f logs/bot.log")
    print()

    print("Useful commands:")
    print("• Start bot: python main.py")
    print("• Stop bot: Ctrl+C")
    print("• Restart bot: sudo systemctl restart telegram-binance-bot")
    print("• Check status: pm2 status")
    print("• View logs: pm2 logs telegram-binance-bot")
    print()

    print("Documentation:")
    print("• README.md - Complete documentation")
    print("• configs/.env.example - Environment variables template")
    print("• docs/ - Additional documentation")
    print()

    print("Support:")
    print("• Issues: Check README.md for troubleshooting")
    print("• GitHub: https://github.com/AdminKroha/telegram-binance-bot")
    print()


def main():
    """Main installation function."""
    print_header()

    # Check Python version
    if not check_python_version():
        return 1

    # Check virtual environment
    check_venv()

    # Create virtual environment (optional)
    if input("\nCreate virtual environment? (y/N): ").lower() == "y":
        create_virtual_env()

    # Install dependencies
    if not install_dependencies():
        return 1

    # Create .env file
    create_env_file()

    # Create directory structure
    create_directory_structure()

    # Setup systemd service (optional)
    if input("\nSetup systemd service? (y/N): ").lower() == "y":
        setup_systemd_service()

    # Setup PM2 (optional)
    if input("\nSetup PM2 process manager? (y/N): ").lower() == "y":
        setup_pm2()

    # Print final instructions
    print_final_instructions()

    print("✅ Installation completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())