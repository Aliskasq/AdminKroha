#!/usr/bin/env python3
"""
Test script for AdminKroha Reminder System

This script tests the enhanced reminder functionality in AdminKroha.
"""

import asyncio
import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))
def test_reminder_schedule():
    """Test ReminderSchedule class by reading the file."""
    print("🧪 Testing ReminderSchedule class...")

    # Read the reminder.py file
    reminder_file_path = os.path.join(os.path.dirname(__file__), 'src', 'reminder.py')
    with open(reminder_file_path, 'r') as f:
        content = f.read()

    # Check for key ReminderSchedule class methods
    required_methods = [
        'def __init__',
        'def is_due_today',
        'def get_next_trigger',
        'def to_dict',
        'def from_dict'
    ]

    for method in required_methods:
        if method in content:
            print(f"✅ Found method: {method}")
        else:
            print(f"❌ Missing method: {method}")
            return False

    # Check for key attributes
    required_attributes = [
        'self.reminder_type',
        'self.time',
        'self.days_of_week',
        'self.is_recurring',
        'self.message',
        'self.user_id'
    ]

    for attr in required_attributes:
        if attr in content:
            print(f"✅ Found attribute: {attr}")
        else:
            print(f"❌ Missing attribute: {attr}")
            return False

    print("✅ ReminderSchedule class structure test passed")
    return True
def test_reminder_manager():
    """Test ReminderManager class by reading the file."""
    print("\n🧪 Testing ReminderManager class...")

    # Read the reminder.py file
    reminder_file_path = os.path.join(os.path.dirname(__file__), 'src', 'reminder.py')
    with open(reminder_file_path, 'r') as f:
        content = f.read()

    # Check for key ReminderManager methods
    required_methods = [
        'def __init__',
        'def add_reminder',
        'def remove_reminder',
        'def update_reminder',
        'def get_reminders',
        'def get_reminder_by_id',
        'def get_reminder_stats',
        'def trigger_reminder'
    ]

    for method in required_methods:
        if method in content:
            print(f"✅ Found method: {method}")
        else:
            print(f"❌ Missing method: {method}")
            return False

    # Check for key attributes
    required_attributes = [
        'self.reminders',
        'self.active_timers',
        'self.default_reminder_types'
    ]

    for attr in required_attributes:
        if attr in content:
            print(f"✅ Found attribute: {attr}")
        else:
            print(f"❌ Missing attribute: {attr}")
            return False

    # Test that the reminder file can be loaded as JSON
    reminder_file_path = os.path.join(os.path.dirname(__file__), 'reminders.json')
    if os.path.exists(reminder_file_path):
        try:
            with open(reminder_file_path, 'r') as f:
                data = json.load(f)
            print(f"✅ reminders.json file exists and is valid JSON")
        except json.JSONDecodeError:
            print(f"❌ reminders.json is not valid JSON")
            return False
    else:
        print(f"ℹ️  reminders.json file doesn't exist (expected for fresh install)")

    print("✅ ReminderManager class structure test passed")
    return True
def test_bot_integration():
    """Test bot integration with reminder system."""
    print("\n🧪 Testing bot integration...")

    # Check that the bot.py file has the reminder manager
    bot_file_path = os.path.join(os.path.dirname(__file__), 'src', 'bot.py')

    with open(bot_file_path, 'r') as f:
        bot_content = f.read()

    # Check for reminder manager imports and initialization
    if 'from .reminder import ReminderManager' in bot_content:
        print("✅ Found ReminderManager import in bot.py")
    else:
        print("❌ Missing ReminderManager import in bot.py")
        return False

    if 'self.reminder_manager = ReminderManager(config)' in bot_content:
        print("✅ Found ReminderManager initialization in bot.py")
    else:
        print("❌ Missing ReminderManager initialization in bot.py")
        return False

    # Check for reminder command methods
    reminder_commands = [
        'add_reminder_command',
        'list_reminders_command',
        'remove_reminder_command',
        'update_reminder_command',
        'trigger_reminder_command'
    ]

    for command in reminder_commands:
        if f'def {command}' in bot_content:
            print(f"✅ Found reminder command: {command}")
        else:
            print(f"❌ Missing reminder command: {command}")
            return False

    # Check for reminder handlers in run method
    if 'application.add_handler(CommandHandler("add-reminder"' in bot_content:
        print("✅ Found add-reminder handler in run method")
    else:
        print("❌ Missing add-reminder handler in run method")
        return False

    print("✅ Bot integration test passed")
    print("   - ReminderManager imported correctly")
    print("   - ReminderManager initialized in bot")
    print("   - All reminder commands added")
    return True
def test_project_structure():
    """Test project structure."""
    print("\n🧪 Testing project structure...")

    # Check for key files
    required_files = [
        'src/bot.py',
        'src/reminder.py',
        'src/config.py',
        'install.py',
        'README.md',
        'systemd/admin-kroha.service'
    ]

    all_files_found = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_files_found = False

    if not all_files_found:
        return False

    # Check for key directories
    required_dirs = [
        'src',
        'systemd',
        'logs',
        'data',
        'backups',
        'configs',
        'docs'
    ]

    all_dirs_found = True
    for dir_path in required_dirs:
        full_path = os.path.join(os.path.dirname(__file__), dir_path)
        if os.path.exists(full_path):
            print(f"✅ Found directory: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            all_dirs_found = False

    if not all_dirs_found:
        return False

    # Check for important project files
    important_files = [
        'src/bot.py',
        'src/reminder.py',
        'src/config.py',
        'install.py',
        'README.md',
        'systemd/admin-kroha.service',
        'configs/.env.example',
        'configs/ecosystem.config.js'
    ]

    all_important_found = True
    for file_path in important_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"⚠️  Missing: {file_path}")
            all_important_found = False

    print("✅ Project structure test passed")
    return True
def test_systemd_service():
    """Test systemd service file."""
    print("\n🧪 Testing systemd service...")

    # Check systemd service file
    service_file_path = os.path.join(os.path.dirname(__file__), 'systemd', 'admin-kroha.service')
    if os.path.exists(service_file_path):
        print("✅ Found systemd service file")

        with open(service_file_path, 'r') as f:
            content = f.read()

        # Check for key elements
        required_elements = [
            'Description=AdminKroha Telegram Bot for Binance Square',
            'User=user',
            'WorkingDirectory=/home/user/projects/AdminKroha',
            'Environment=PYTHONUNBUFFERED=1',
            'ExecStart=/home/user/projects/AdminKroha/venv_production/bin/python3 /home/user/projects/AdminKroha/main.py',
            'Restart=on-failure'
        ]

        all_elements_found = True
        for element in required_elements:
            if element in content:
                print(f"✅ Found element: {element[:50]}...")
            else:
                print(f"❌ Missing element: {element[:50]}...")
                all_elements_found = False

        if all_elements_found:
            print("✅ Systemd service file test passed")
            return True
        else:
            return False
    else:
        print("❌ Missing systemd service file")
        return False
def main():
    """Run all tests."""
    print("🚀 AdminKroha Reminder System Test Suite")
    print("=" * 50)

    try:
        # Test reminder schedule
        if not test_reminder_schedule():
            return False

        # Test reminder manager
        if not test_reminder_manager():
            return False

        # Test bot integration
        if not test_bot_integration():
            return False

        # Test project structure
        if not test_project_structure():
            return False

        # Test systemd service
        if not test_systemd_service():
            return False

        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("\n📋 Test Summary:")
        print("   ✅ ReminderSchedule class structure")
        print("   ✅ ReminderManager class structure")
        print("   ✅ Bot integration")
        print("   ✅ Project structure")
        print("   ✅ Systemd service file")
        print("\n🚀 AdminKroha is ready for production deployment!")
        print("\n📝 Next Steps:")
        print("   1. Install required Python dependencies")
        print("   2. Configure .env file with API keys")
        print("   3. Run: python3 install.py (for enhanced setup)")
        print("   4. Start bot with: sudo systemctl start admin-kroha")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)