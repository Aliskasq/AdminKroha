"""
Reminder system for Telegram Binance Bot.

This module provides a flexible reminder system with customizable time and days of the week.
It allows users to set up recurring notifications and task reminders.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import json
import re
from enum import Enum

from .config import Config
from .logger import setup_logger

logger = setup_logger(__name__)
class ReminderType(Enum):
    """Types of reminders."""
    TASK = "task"
    MARKET = "market"
    ANALYSIS = "analysis"
    NEWS = "news"
    GENERAL = "general"
class ReminderSchedule:
    """Represents a reminder schedule configuration."""

    def __init__(
        self,
        reminder_type: str,
        time: str,
        days_of_week: Optional[List[int]] = None,
        is_recurring: bool = True,
        message: str = "",
        user_id: Optional[int] = None,
        reminder_id: Optional[str] = None
    ):
        """
        Initialize a reminder schedule.

        Args:
            reminder_type: Type of reminder (task, market, analysis, news, general)
            time: Time in HH:MM format (24-hour)
            days_of_week: List of days (0=Monday, 6=Sunday). If None, every day
            is_recurring: Whether the reminder repeats
            message: Custom message for the reminder
            user_id: User who created the reminder
            reminder_id: Unique ID for the reminder
        """
        self.reminder_type = reminder_type
        self.time = time
        self.days_of_week = days_of_week or [0, 1, 2, 3, 4, 5, 6]  # Every day by default
        self.is_recurring = is_recurring
        self.message = message
        self.user_id = user_id
        self.reminder_id = reminder_id or f"rem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id or 'system'}"
        self.last_triggered = None
        self.next_triggered = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def is_due_today(self) -> bool:
        """
        Check if reminder should be triggered today.

        Returns:
            True if reminder should be triggered today
        """
        if not self.is_recurring:
            return True

        current_day = datetime.now().weekday()
        return current_day in self.days_of_week

    def get_next_trigger(self) -> datetime:
        """
        Get the next trigger time for this reminder.

        Returns:
            Next trigger datetime
        """
        now = datetime.now()
        current_time_str = now.strftime('%H:%M')

        # Parse the reminder time
        try:
            hour, minute = map(int, self.time.split(':'))
        except ValueError:
            hour, minute = 9, 0  # Default to 9:00 if invalid

        # Check if we should trigger today
        if self.is_due_today():
            today_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If the time has passed today, schedule for tomorrow
            if today_trigger <= now:
                today_trigger += timedelta(days=1)

            # If today is not in the schedule, skip to next scheduled day
            if current_day not in self.days_of_week:
                # Find next scheduled day
                days_ahead = 0
                while True:
                    next_day = (current_day + days_ahead) % 7
                    if next_day in self.days_of_week:
                        days_ahead += 1
                        break
                    days_ahead += 1
                today_trigger += timedelta(days=days_ahead)

            return today_trigger
        else:
            # Find next scheduled day
            days_ahead = 0
            while True:
                next_day = (current_day + days_ahead) % 7
                if next_day in self.days_of_week:
                    days_ahead += 1
                    break
                days_ahead += 1

            next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_trigger += timedelta(days=days_ahead)

            return next_trigger

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert reminder to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'reminder_type': self.reminder_type,
            'time': self.time,
            'days_of_week': self.days_of_week,
            'is_recurring': self.is_recurring,
            'message': self.message,
            'user_id': self.user_id,
            'reminder_id': self.reminder_id,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'next_triggered': self.next_triggered.isoformat() if self.next_triggered else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReminderSchedule':
        """
        Create reminder from dictionary.

        Args:
            data: Dictionary with reminder data

        Returns:
            ReminderSchedule instance
        """
        reminder = cls(
            reminder_type=data['reminder_type'],
            time=data['time'],
            days_of_week=data['days_of_week'],
            is_recurring=data['is_recurring'],
            message=data['message'],
            user_id=data['user_id'],
            reminder_id=data['reminder_id']
        )

        if data['last_triggered']:
            reminder.last_triggered = datetime.fromisoformat(data['last_triggered'])
        if data['next_triggered']:
            reminder.next_triggered = datetime.fromisoformat(data['next_triggered'])
        reminder.created_at = datetime.fromisoformat(data['created_at'])
        reminder.updated_at = datetime.fromisoformat(data['updated_at'])

        return reminder
class ReminderManager:
    """Manages user reminders with customizable schedules."""

    def __init__(self, config: Config):
        """
        Initialize reminder manager.

        Args:
            config: Bot configuration
        """
        self.config = config
        self.reminders: Dict[int, List[ReminderSchedule]] = {}  # user_id -> list of reminders
        self.active_timers: Dict[str, asyncio.Task] = {}
        self.default_reminder_types = {
            'task': 'Task reminder: {message}',
            'market': 'Market update: {message}',
            'analysis': 'Analysis reminder: {message}',
            'news': 'News update: {message}',
            'general': 'Reminder: {message}'
        }

        # Load saved reminders
        self._load_reminders()

    async def add_reminder(
        self,
        reminder_type: str,
        time: str,
        days_of_week: Optional[List[int]] = None,
        is_recurring: bool = True,
        message: str = "",
        user_id: Optional[int] = None
    ) -> str:
        """
        Add a new reminder.

        Args:
            reminder_type: Type of reminder
            time: Time in HH:MM format
            days_of_week: Days to trigger (0=Monday, 6=Sunday)
            is_recurring: Whether reminder repeats
            message: Custom message
            user_id: User ID

        Returns:
            Reminder ID
        """
        # Validate reminder type
        if reminder_type not in self.default_reminder_types:
            reminder_type = 'general'

        # Use default message if none provided
        if not message:
            message = self.default_reminder_types[reminder_type]

        # Create reminder
        reminder = ReminderSchedule(
            reminder_type=reminder_type,
            time=time,
            days_of_week=days_of_week,
            is_recurring=is_recurring,
            message=message,
            user_id=user_id
        )

        # Add to user's reminders
        if user_id not in self.reminders:
            self.reminders[user_id] = []

        self.reminders[user_id].append(reminder)

        # Schedule the reminder
        await self._schedule_reminder(reminder)

        # Save reminders
        await self._save_reminders()

        logger.info(f"Added reminder {reminder.reminder_id} for user {user_id}")
        return reminder.reminder_id

    async def remove_reminder(self, reminder_id: str, user_id: Optional[int] = None) -> bool:
        """
        Remove a reminder.

        Args:
            reminder_id: ID of reminder to remove
            user_id: User ID (optional, will search all users if not provided)

        Returns:
            True if reminder was removed, False otherwise
        """
        # Cancel any active timer for this reminder
        if reminder_id in self.active_timers:
            self.active_timers[reminder_id].cancel()
            del self.active_timers[reminder_id]

        # Find and remove the reminder
        if user_id:
            user_reminders = self.reminders.get(user_id, [])
            for reminder in user_reminders[:]:
                if reminder.reminder_id == reminder_id:
                    user_reminders.remove(reminder)
                    self.reminders[user_id] = user_reminders
                    if not user_reminders:
                        del self.reminders[user_id]
                    break
        else:
            # Search all users
            for uid, user_reminders in self.reminders.items():
                for reminder in user_reminders[:]:
                    if reminder.reminder_id == reminder_id:
                        user_reminders.remove(reminder)
                        self.reminders[uid] = user_reminders
                        if not user_reminders:
                            del self.reminders[uid]
                        break

        # Save reminders
        await self._save_reminders()

        logger.info(f"Removed reminder {reminder_id}")
        return True

    async def update_reminder(
        self,
        reminder_id: str,
        updates: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> bool:
        """
        Update a reminder.

        Args:
            reminder_id: ID of reminder to update
            updates: Dictionary of updates to apply
            user_id: User ID (optional)

        Returns:
            True if reminder was updated, False otherwise
        """
        # Find the reminder
        reminder = self._find_reminder(reminder_id, user_id)
        if not reminder:
            return False

        # Cancel existing timer
        if reminder.reminder_id in self.active_timers:
            self.active_timers[reminder.reminder_id].cancel()
            del self.active_timers[reminder.reminder_id]

        # Apply updates
        if 'time' in updates:
            reminder.time = updates['time']
        if 'days_of_week' in updates:
            reminder.days_of_week = updates['days_of_week']
        if 'is_recurring' in updates:
            reminder.is_recurring = updates['is_recurring']
        if 'message' in updates:
            reminder.message = updates['message']

        reminder.updated_at = datetime.now()

        # Reschedule the reminder
        await self._schedule_reminder(reminder)

        # Save reminders
        await self._save_reminders()

        logger.info(f"Updated reminder {reminder_id}")
        return True

    async def get_reminders(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get reminders for a user or all users.

        Args:
            user_id: User ID (optional)

        Returns:
            List of reminder dictionaries
        """
        if user_id:
            reminders = self.reminders.get(user_id, [])
        else:
            reminders = []
            for uid, user_reminders in self.reminders.items():
                reminders.extend(user_reminders)

        return [reminder.to_dict() for reminder in reminders]

    async def get_reminder_by_id(self, reminder_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific reminder by ID.

        Args:
            reminder_id: Reminder ID
            user_id: User ID (optional)

        Returns:
            Reminder dictionary or None
        """
        reminder = self._find_reminder(reminder_id, user_id)
        if reminder:
            return reminder.to_dict()
        return None

    async def trigger_reminder(self, reminder_id: str) -> bool:
        """
        Trigger a reminder manually.

        Args:
            reminder_id: Reminder ID

        Returns:
            True if reminder was triggered, False otherwise
        """
        reminder = self._find_reminder_by_id(reminder_id)
        if not reminder:
            return False

        # Mark as triggered
        reminder.last_triggered = datetime.now()
        reminder.next_triggered = reminder.get_next_trigger()
        reminder.updated_at = datetime.now()

        # Save reminders
        await self._save_reminders()

        # Send reminder to user (if we have the user_id)
        if reminder.user_id:
            await self._send_reminder_message(reminder)

        logger.info(f"Triggered reminder {reminder_id}")
        return True

    def get_reminder_stats(self) -> Dict[str, Any]:
        """
        Get reminder statistics.

        Returns:
            Statistics dictionary
        """
        total_reminders = sum(len(reminders) for reminders in self.reminders.values())
        recurring_reminders = 0
        today_due = 0

        for user_reminders in self.reminders.values():
            for reminder in user_reminders:
                if reminder.is_recurring:
                    recurring_reminders += 1
                if reminder.is_due_today():
                    today_due += 1

        return {
            'total_reminders': total_reminders,
            'recurring_reminders': recurring_reminders,
            'today_due': today_due,
            'users_with_reminders': len(self.reminders)
        }

    async def cleanup_expired_reminders(self):
        """
        Clean up expired reminders (reminders with no users).
        """
        # Remove empty user lists
        users_to_remove = [uid for uid, reminders in self.reminders.items() if not reminders]
        for uid in users_to_remove:
            del self.reminders[uid]

        await self._save_reminders()

    async def _schedule_reminder(self, reminder: ReminderSchedule):
        """
        Schedule a reminder task.

        Args:
            reminder: Reminder to schedule
        """
        # Cancel existing timer
        if reminder.reminder_id in self.active_timers:
            self.active_timers[reminder.reminder_id].cancel()

        # Schedule new reminder
        next_trigger = reminder.get_next_trigger()
        now = datetime.now()

        if next_trigger > now:
            delay = (next_trigger - now).total_seconds()
            task = asyncio.create_task(self._reminder_task(reminder.reminder_id, delay))
            self.active_timers[reminder.reminder_id] = task
        else:
            # Trigger immediately if past due
            asyncio.create_task(self._send_reminder_message(reminder))

    async def _reminder_task(self, reminder_id: str, delay: float):
        """
        Task that runs when a reminder is due.

        Args:
            reminder_id: Reminder ID
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)

        # Check if reminder still exists
        reminder = self._find_reminder_by_id(reminder_id)
        if not reminder:
            return

        # Mark as triggered
        reminder.last_triggered = datetime.now()
        reminder.next_triggered = reminder.get_next_trigger()
        reminder.updated_at = datetime.now()

        # Send reminder message
        await self._send_reminder_message(reminder)

        # Reschedule if recurring
        if reminder.is_recurring:
            await self._schedule_reminder(reminder)

        # Save reminders
        await self._save_reminders()

    async def _send_reminder_message(self, reminder: ReminderSchedule):
        """
        Send reminder message to user.

        Args:
            reminder: Reminder to send
        """
        # Format the reminder message
        message = reminder.message.format(
            reminder_type=reminder.reminder_type,
            time=reminder.time,
            days_of_week=', '.join([self._day_name(day) for day in reminder.days_of_week])
        )

        # Add emoji based on reminder type
        emoji_map = {
            'task': '✅',
            'market': '📊',
            'analysis': '📈',
            'news': '📰',
            'general': '🔔'
        }

        emoji = emoji_map.get(reminder.reminder_type, '🔔')

        # Format the reminder with emoji and metadata
        formatted_message = (
            f"{emoji} **Reminder ({reminder.reminder_type.title()})** \n\n"
            f"⏰ **Time:** {reminder.time} \n"
            f"📅 **Days:** {', '.join([self._day_name(day) for day in reminder.days_of_week])} \n"
            f"💬 **Message:** {message}\n\n"
            f"📍 **Reminder ID:** {reminder.reminder_id}\n"
            f"📅 **Created:** {reminder.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        # For now, we'll just log the reminder
        # In a real implementation, this would send a message via Telegram
        logger.info(f"Reminder for user {reminder.user_id}: {formatted_message}")

    def _find_reminder(self, reminder_id: str, user_id: Optional[int] = None) -> Optional[ReminderSchedule]:
        """
        Find a reminder by ID.

        Args:
            reminder_id: Reminder ID
            user_id: User ID (optional)

        Returns:
            Reminder or None
        """
        if user_id:
            user_reminders = self.reminders.get(user_id, [])
            for reminder in user_reminders:
                if reminder.reminder_id == reminder_id:
                    return reminder
        else:
            for user_reminders in self.reminders.values():
                for reminder in user_reminders:
                    if reminder.reminder_id == reminder_id:
                        return reminder

        return None

    def _find_reminder_by_id(self, reminder_id: str) -> Optional[ReminderSchedule]:
        """
        Find a reminder by ID (search all users).

        Args:
            reminder_id: Reminder ID

        Returns:
            Reminder or None
        """
        return self._find_reminder(reminder_id, None)

    def _day_name(self, day_index: int) -> str:
        """
        Get day name from day index.

        Args:
            day_index: Day index (0=Monday, 6=Sunday)

        Returns:
            Day name
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[day_index % 7]

    async def _save_reminders(self):
        """Save reminders to file."""
        try:
            all_reminders = []
            for user_id, user_reminders in self.reminders.items():
                for reminder in user_reminders:
                    reminder_dict = reminder.to_dict()
                    reminder_dict['user_id'] = user_id
                    all_reminders.append(reminder_dict)

            with open('reminders.json', 'w') as f:
                json.dump(all_reminders, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")

    async def _load_reminders(self):
        """Load reminders from file."""
        try:
            if os.path.exists('reminders.json'):
                with open('reminders.json', 'r') as f:
                    all_reminders = json.load(f)

                # Clear existing reminders
                self.reminders.clear()

                # Load reminders
                for reminder_dict in all_reminders:
                    user_id = reminder_dict.pop('user_id')
                    reminder = ReminderSchedule.from_dict(reminder_dict)

                    if user_id not in self.reminders:
                        self.reminders[user_id] = []

                    self.reminders[user_id].append(reminder)

                    # Reschedule reminders
                    await self._schedule_reminder(reminder)

                logger.info(f"Loaded {len(all_reminders)} reminders")

        except Exception as e:
            logger.error(f"Failed to load reminders: {e}")