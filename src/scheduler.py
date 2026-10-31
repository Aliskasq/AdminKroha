"""
Post scheduling for Telegram Binance Bot.

This module handles scheduling posts for future publication to Binance Square.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

from .config import Config
from .binance_api import BinanceSquareAPI

logger = logging.getLogger(__name__)


class PostScheduler:
    """Manages scheduled posts for Telegram Binance Bot."""

    def __init__(self, config: Config, binance_api: BinanceSquareAPI):
        """
        Initialize post scheduler.

        Args:
            config: Bot configuration
            binance_api: Binance API client
        """
        self.config = config
        self.binance_api = binance_api
        self.scheduled_posts: List[Dict[str, Any]] = []
        self.pending_posts: List[Dict[str, Any]] = []
        self.max_pending_posts = 100
        self.check_interval = 60  # seconds

    async def schedule_post(
        self,
        scheduled_time: datetime,
        content: str,
        user_id: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a post for future publication.

        Args:
            scheduled_time: When to publish the post
            content: Content to post
            user_id: User who scheduled the post
            options: Additional post options

        Returns:
            Post ID
        """
        post_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id or 'system'}"

        post = {
            'id': post_id,
            'scheduled_time': scheduled_time,
            'content': content,
            'user_id': user_id,
            'status': 'scheduled',
            'created_at': datetime.now(),
            'options': options or {}
        }

        self.scheduled_posts.append(post)

        # Save to file
        await self._save_scheduled_posts()

        logger.info(f"Post scheduled: {post_id} at {scheduled_time}")
        return post_id

    async def process_pending_posts(self) -> List[str]:
        """
        Process posts that are due to be published.

        Returns:
            List of published post IDs
        """
        published_posts = []
        current_time = datetime.now()

        for post in self.scheduled_posts[:]:
            if post['status'] == 'scheduled' and post['scheduled_time'] <= current_time:
                try:
                    # Publish the post
                    result = await self._publish_scheduled_post(post)
                    published_posts.append(post['id'])

                    # Update post status
                    post['status'] = 'published'
                    post['published_at'] = current_time

                except Exception as e:
                    logger.error(f"Failed to publish scheduled post {post['id']}: {e}")
                    post['status'] = 'failed'
                    post['error'] = str(e)

        # Save updated posts
        await self._save_scheduled_posts()
        return published_posts

    async def _publish_scheduled_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a scheduled post.

        Args:
            post: Post data

        Returns:
            Post result from Binance API
        """
        content = post['content']

        # Determine post type
        post_type = self._detect_post_type(content)

        # Prepare options
        options = post.get('options', {})

        # Post to Binance
        result = await self.binance_api.post_content(
            content,
            post_type=post_type,
            tags=options.get('tags'),
            poll=options.get('poll')
        )

        # Add image if specified
        if options.get('image_url'):
            image_result = await self.binance_api.upload_image(
                open(options['image_url'], 'rb').read()
            )

        logger.info(f"Published scheduled post: {post['id']}")
        return result

    def _detect_post_type(self, content: str) -> str:
        """
        Detect post type based on content.

        Args:
            content: Content text

        Returns:
            Detected post type
        """
        # Simple heuristics for post type detection
        if any(word in content.lower() for word in ['image', 'photo', 'picture', 'img', '📸']):
            return 'image'

        if any(word in content.lower() for word in ['poll', 'vote', 'option', 'choice', '🗳️']):
            return 'poll'

        return 'text'

    async def _save_scheduled_posts(self):
        """Save scheduled posts to file."""
        try:
            # Convert posts to serializable format
            serialized_posts = []
            for post in self.scheduled_posts:
                serialized_post = post.copy()
                serialized_post['scheduled_time'] = serialized_post['scheduled_time'].isoformat()
                serialized_post['created_at'] = serialized_post['created_at'].isoformat()
                if 'published_at' in serialized_post:
                    serialized_post['published_at'] = serialized_post['published_at'].isoformat()
                serialized_posts.append(serialized_post)

            # Save to file
            with open('scheduled_posts.json', 'w') as f:
                json.dump(serialized_posts, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save scheduled posts: {e}")

    async def load_scheduled_posts(self):
        """Load scheduled posts from file."""
        try:
            if os.path.exists('scheduled_posts.json'):
                with open('scheduled_posts.json', 'r') as f:
                    serialized_posts = json.load(f)

                # Convert back to proper format
                self.scheduled_posts = []
                for post in serialized_posts:
                    deserialized_post = post.copy()
                    deserialized_post['scheduled_time'] = datetime.fromisoformat(deserialized_post['scheduled_time'])
                    deserialized_post['created_at'] = datetime.fromisoformat(deserialized_post['created_at'])
                    if 'published_at' in deserialized_post:
                        deserialized_post['published_at'] = datetime.fromisoformat(deserialized_post['published_at'])
                    self.scheduled_posts.append(deserialized_post)

                logger.info(f"Loaded {len(self.scheduled_posts)} scheduled posts")

        except Exception as e:
            logger.error(f"Failed to load scheduled posts: {e}")

    async def cancel_scheduled_post(self, post_id: str) -> bool:
        """
        Cancel a scheduled post.

        Args:
            post_id: ID of post to cancel

        Returns:
            True if successful, False otherwise
        """
        for post in self.scheduled_posts:
            if post['id'] == post_id:
                if post['status'] == 'scheduled':
                    post['status'] = 'cancelled'
                    await self._save_scheduled_posts()
                    logger.info(f"Cancelled scheduled post: {post_id}")
                    return True
                else:
                    logger.warning(f"Cannot cancel post {post_id} - status: {post['status']}")
                    return False

        logger.warning(f"Scheduled post not found: {post_id}")
        return False

    def get_scheduled_posts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get scheduled posts with optional status filter.

        Args:
            status: Status filter (scheduled, published, failed, cancelled)

        Returns:
            List of scheduled posts
        """
        if status is None:
            return self.scheduled_posts.copy()

        return [post for post in self.scheduled_posts if post['status'] == status]

    def get_scheduling_stats(self) -> Dict[str, Any]:
        """
        Get scheduling statistics.

        Returns:
            Statistics dictionary
        """
        current_time = datetime.now()
        upcoming = 0
        published = 0
        failed = 0
        cancelled = 0

        for post in self.scheduled_posts:
            if post['status'] == 'scheduled':
                if post['scheduled_time'] > current_time:
                    upcoming += 1
                else:
                    upcoming += 1  # Missed posts
            elif post['status'] == 'published':
                published += 1
            elif post['status'] == 'failed':
                failed += 1
            elif post['status'] == 'cancelled':
                cancelled += 1

        return {
            'total': len(self.scheduled_posts),
            'scheduled': upcoming + published,
            'published': published,
            'failed': failed,
            'cancelled': cancelled,
            'upcoming': upcoming
        }

    async def cleanup_old_posts(self, days: int = 30):
        """
        Clean up old posts.

        Args:
            days: Number of days to keep posts
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        self.scheduled_posts = [
            post for post in self.scheduled_posts
            if datetime.fromisoformat(post['created_at']) > cutoff_time
        ]

        await self._save_scheduled_posts()
        logger.info(f"Cleaned up old posts, remaining: {len(self.scheduled_posts)}")