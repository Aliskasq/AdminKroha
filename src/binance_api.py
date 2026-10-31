"""
Binance Square API integration for Telegram bot.

This module handles all interactions with the Binance Square API,
including posting content, uploading images, and retrieving ticker data.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
import json
import base64
from datetime import datetime

import aiohttp
from aiohttp import ClientSession, ClientResponseError

from .config import Config

logger = logging.getLogger(__name__)


class BinanceSquareAPI:
    """Binance Square API client for Telegram bot."""

    def __init__(self, config: Config):
        """
        Initialize Binance Square API client.

        Args:
            config: Bot configuration
        """
        self.config = config
        self.session: Optional[ClientSession] = None
        self.base_url = "https://api.binance.com"
        self.square_url = "https://api.binance.com/square/api/v1"
        self.max_retries = 3
        self.retry_delay = 1.0

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _create_session(self):
        """Create HTTP session with proper headers and timeouts."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        headers = {
            'X-Square-OpenAPI-Key': self.config.binance_api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'Telegram-Binance-Bot/1.0.0',
            'Accept': 'application/json',
        }

        self.session = ClientSession(
            timeout=timeout,
            headers=headers,
            connector=aiohttp.TCPConnector(limit=self.config.max_concurrent_requests)
        )

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            data: Request body
            params: Query parameters
            max_retries: Maximum number of retries

        Returns:
            Response data as dictionary

        Raises:
            Exception: If request fails after all retries
        """
        if not self.session:
            await self._create_session()

        retries = max_retries or self.max_retries
        last_exception = None

        for attempt in range(retries):
            try:
                async with self.session.request(
                    method, url, json=data, params=params
                ) as response:
                    # Handle different response types
                    if response.content_type == 'application/json':
                        response_data = await response.json()
                    else:
                        response_text = await response.text()
                        response_data = {'error': response_text}

                    # Check if response indicates an error
                    if response.status >= 400:
                        error_msg = (
                            f"HTTP {response.status}: {response_data.get('message', 'Unknown error')}"
                        )
                        raise ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_msg,
                            headers=response.headers,
                        )

                    return response_data

            except Exception as e:
                last_exception = e
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                continue

        raise last_exception or Exception("Request failed after all retries")

    async def post_content(
        self,
        content: str,
        post_type: str = 'text',
        image_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        poll: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Post content to Binance Square.

        Args:
            content: Content text
            post_type: Type of post (text, image, article)
            image_url: URL of image (for image posts)
            tags: List of hashtags
            poll: Poll data (for polls)

        Returns:
            Response data from Binance API
        """
        # Prepare request data
        data = {
            'content': content,
            'postType': post_type,
            'timestamp': datetime.now().isoformat()
        }

        # Add optional fields
        if image_url:
            data['imageUrl'] = image_url

        if tags:
            data['tags'] = tags

        if poll:
            data['poll'] = poll

        try:
            response = await self._request(
                'POST',
                f'{self.square_url}/content/add',
                data=data
            )

            logger.info(f"Content posted successfully: {response.get('id', 'N/A')}")
            return response

        except Exception as e:
            logger.error(f"Failed to post content: {e}")
            raise

    async def upload_image(
        self,
        image_data: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload image to Binance Square.

        Args:
            image_data: Image bytes
            filename: Optional filename

        Returns:
            Upload response with image URL
        """
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Prepare upload data
        data = {
            'image': image_base64,
            'contentType': 'image/jpeg'
        }

        if filename:
            data['filename'] = filename

        try:
            response = await self._request(
                'POST',
                f'{self.square_url}/content/image/upload',
                data=data
            )

            logger.info(f"Image uploaded successfully: {response.get('url', 'N/A')}")
            return response

        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            raise

    async def get_ticker_data(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get cryptocurrency ticker data from Binance.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dictionary of ticker data
        """
        try:
            # Convert symbols to Binance format (remove USDT suffix for some endpoints)
            formatted_symbols = []
            for symbol in symbols:
                if symbol.endswith('USDT'):
                    formatted_symbols.append(symbol[:-4] + 'BTC')  # Convert to BTC pair for some endpoints
                else:
                    formatted_symbols.append(symbol)

            params = {'symbols': formatted_symbols}
            response = await self._request('GET', f'{self.base_url}/api/v3/ticker/24hr', params=params)

            # Process and format the ticker data
            ticker_data = {}
            for item in response:
                symbol = item.get('symbol')
                if symbol in symbols:
                    ticker_data[symbol] = {
                        'symbol': symbol,
                        'price': float(item.get('lastPrice', 0)),
                        'change24h': float(item.get('priceChangePercent', 0)),
                        'high24h': float(item.get('highPrice', 0)),
                        'low24h': float(item.get('lowPrice', 0)),
                        'volume': float(item.get('volume', 0)),
                        'quoteVolume': float(item.get('quoteVolume', 0)),
                        'openPrice': float(item.get('openPrice', 0)),
                        'prevClosePrice': float(item.get('prevClosePrice', 0)),
                        'count': int(item.get('count', 0)),
                        'weightAvgPrice': float(item.get('weightAvgPrice', 0)),
                        'askPrice': float(item.get('askPrice', 0)),
                        'askQty': float(item.get('askQty', 0)),
                        'bidPrice': float(item.get('bidPrice', 0)),
                        'bidQty': float(item.get('bidQty', 0)),
                        'timestamp': int(item.get('time', 0)),
                        'datetime': datetime.fromtimestamp(item.get('time', 0) / 1000).isoformat()
                    }

            logger.info(f"Retrieved ticker data for {len(ticker_data)} symbols")
            return ticker_data

        except Exception as e:
            logger.error(f"Failed to get ticker data: {e}")
            raise

    async def create_poll(
        self,
        question: str,
        options: List[str],
        duration: Optional[int] = None,
        anonymous: bool = True
    ) -> Dict[str, Any]:
        """
        Create a poll in Binance Square.

        Args:
            question: Poll question
            options: List of poll options
            duration: Poll duration in seconds (optional)
            anonymous: Whether poll is anonymous

        Returns:
            Poll response data
        """
        data = {
            'question': question,
            'options': options,
            'anonymous': anonymous,
            'createdAt': datetime.now().isoformat()
        }

        if duration:
            data['duration'] = duration

        try:
            response = await self._request(
                'POST',
                f'{self.square_url}/content/poll',
                data=data
            )

            logger.info(f"Poll created successfully: {response.get('id', 'N/A')}")
            return response

        except Exception as e:
            logger.error(f"Failed to create poll: {e}")
            raise

    async def get_user_posts(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's posts from Binance Square.

        Args:
            limit: Number of posts to retrieve
            offset: Offset for pagination

        Returns:
            List of post data
        """
        params = {'limit': limit, 'offset': offset}

        try:
            response = await self._request(
                'GET',
                f'{self.square_url}/content/user/posts',
                params=params
            )

            logger.info(f"Retrieved {len(response)} user posts")
            return response

        except Exception as e:
            logger.error(f"Failed to get user posts: {e}")
            raise

    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from Binance Square.

        Args:
            post_id: ID of the post to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self._request(
                'DELETE',
                f'{self.square_url}/content/{post_id}'
            )

            logger.info(f"Post deleted successfully: {post_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            return False

    async def get_square_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Binance Square usage.

        Returns:
            Statistics data
        """
        try:
            response = await self._request(
                'GET',
                f'{self.square_url}/content/stats'
            )

            logger.info("Retrieved Binance Square statistics")
            return response

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise