"""
Binance Square API integration for Telegram bot.

This module handles all interactions with the Binance Square API,
including posting content, uploading images, and retrieving ticker data.

Uses the official Binance Square OpenAPI v1/v2 endpoints:
- Text posts: POST https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add
- Image upload: 4-step flow via v2 endpoints
- Ticker data: GET https://api.binance.com/api/v3/ticker/24hr
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
        self.openapi_url = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi"
        self.openapi_v2_url = "https://www.binance.com/bapi/composite/v2/public/pgc/openApi"
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
            'clienttype': 'binanceSkill',
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
        max_retries: Optional[int] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            data: Request body
            params: Query parameters
            max_retries: Maximum number of retries
            headers: Additional headers to add to request

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
                request_headers = {}
                if headers:
                    request_headers.update(headers)

                async with self.session.request(
                    method, url, json=data, params=params, headers=request_headers
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

                    # Handle Binance API error codes
                    if isinstance(response_data, dict) and response_data.get('code') != '000000':
                        error_code = response_data.get('code', 'Unknown')
                        error_msg = response_data.get('message', 'Unknown error')
                        logger.warning(f"Binance API error {error_code}: {error_msg}")
                        # For some errors like 504 on content/add, treat as success per official helper
                        if error_code == '504' and 'content/add' in url:
                            return response_data
                        # For other errors, raise exception
                        raise Exception(f"Binance API error {error_code}: {error_msg}")

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
        image_list: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        poll: Optional[Dict] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post content to Binance Square.

        Args:
            content: Content text
            post_type: Type of post (text, image, article)
            image_url: Single image URL (used as cover for articles)
            image_list: List of image URLs (up to 4 for posts)
            tags: List of hashtags (not used in new API, embed in content)
            poll: Poll data (for polls)

        Returns:
            Response data from Binance API with post ID
        """
        # Determine content type based on post_type
        if post_type == 'article':
            content_type = 2
        else:
            content_type = 1

        # Prepare request data for new API format
        data = {
            'contentType': content_type,
            'bodyTextOnly': content
        }

        # Add title for articles (required by Binance API for contentType=2)
        if post_type == 'article' and title:
            data['title'] = title

        # Add images based on post type
        if post_type == 'article':
            # Articles use cover image (single)
            if image_url:
                data['cover'] = image_url
        else:
            # Regular posts use imageList (up to 4)
            if image_list:
                data['imageList'] = image_list[:4]  # Max 4 images
            elif image_url:
                data['imageList'] = [image_url]

        try:
            response = await self._request(
                'POST',
                f'{self.openapi_url}/content/add',
                data=data
            )

            post_id = response.get('data', {}).get('id', 'N/A')
            logger.info(f"Content posted successfully: {post_id}")
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
        Upload image to Binance Square using the 4-step v2 flow.

        Args:
            image_data: Image bytes
            filename: Optional filename

        Returns:
            Dictionary with image URL
        """
        if not filename:
            filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Step 1: Get presigned URL
        try:
            presigned_response = await self._request(
                'POST',
                f'{self.openapi_v2_url}/image/presignedUrl',
                data={'imageName': filename}
            )

            presigned_data = presigned_response.get('data', {})
            presigned_url = presigned_data.get('presignedUrl')
            file_ticket = presigned_data.get('fileTicket')

            if not presigned_url or not file_ticket:
                raise Exception(f"Failed to get presigned URL: {presigned_response}")

            logger.info(f"Got presigned URL for image upload")

        except Exception as e:
            logger.error(f"Failed to get presigned URL: {e}")
            raise

        # Step 2: Upload image to presigned URL (PUT request)
        try:
            content_type = 'image/jpeg'
            if filename.lower().endswith('.png'):
                content_type = 'image/png'
            elif filename.lower().endswith('.gif'):
                content_type = 'image/gif'
            elif filename.lower().endswith('.webp'):
                content_type = 'image/webp'

            # Use a separate request for the PUT to presigned URL
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            async with aiohttp.ClientSession(timeout=timeout) as upload_session:
                async with upload_session.put(
                    presigned_url,
                    data=image_data,
                    headers={'Content-Type': content_type}
                ) as response:
                    if response.status >= 400:
                        raise Exception(f"Image upload to presigned URL failed: HTTP {response.status}")

            logger.info(f"Image uploaded to presigned URL successfully")

        except Exception as e:
            logger.error(f"Failed to upload image to presigned URL: {e}")
            raise

        # Step 3: Poll image status
        image_url = await self._poll_image_status(file_ticket)
        if not image_url:
            raise Exception("Image processing timed out or failed")

        logger.info(f"Image processed successfully: {image_url}")
        return {'url': image_url}

    async def _poll_image_status(self, file_ticket: str, max_attempts: int = 10, delay: int = 3) -> Optional[str]:
        """
        Poll image processing status.

        Args:
            file_ticket: File ticket from presigned URL response
            max_attempts: Maximum polling attempts
            delay: Delay between attempts in seconds

        Returns:
            Image URL if successful, None otherwise
        """
        for attempt in range(max_attempts):
            try:
                status_response = await self._request(
                    'POST',
                    f'{self.openapi_v2_url}/image/imageStatus',
                    data={'fileTicket': file_ticket}
                )

                status_data = status_response.get('data', {})
                status = status_data.get('status')
                image_url = status_data.get('imageUrl')

                if status == 1 and image_url:  # Success
                    return image_url
                elif status == 2:  # Failed
                    logger.error(f"Image processing failed: {status_data}")
                    return None
                elif status == 0:  # Processing
                    logger.debug(f"Image processing... attempt {attempt + 1}/{max_attempts}")
                    await asyncio.sleep(delay)
                    continue

            except Exception as e:
                logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay)
                continue

        logger.error(f"Image polling timed out after {max_attempts} attempts")
        return None

    async def post_image_content(
        self,
        content: str,
        image_data: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post content with image in one go (uploads image then posts).

        Args:
            content: Post text content
            image_data: Image bytes
            filename: Optional filename

        Returns:
            Response data from Binance API
        """
        # Upload image first
        upload_result = await self.upload_image(image_data, filename)
        image_url = upload_result.get('url')

        if not image_url:
            raise Exception("Failed to upload image")

        # Post content with image
        return await self.post_content(content, image_list=[image_url])

    async def create_poll(
        self,
        question: str,
        options: List[str],
        duration: Optional[int] = None,
        anonymous: bool = True
    ) -> Dict[str, Any]:
        """
        Create a poll in Binance Square.
        Note: Polls may require different API format, using content post for now.

        Args:
            question: Poll question
            options: List of poll options
            duration: Poll duration in seconds (optional)
            anonymous: Whether poll is anonymous

        Returns:
            Poll response data
        """
        # For now, create as a text post with poll info
        # The actual poll API might be different
        poll_text = f"🗳️ **Опрос:** {question}\n\n"
        for i, option in enumerate(options, 1):
            poll_text += f"{i}. {option}\n"

        return await self.post_content(poll_text)

    async def get_user_posts(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's posts from Binance Square.
        Note: Endpoint might be different in new API.

        Args:
            limit: Number of posts to retrieve
            offset: Offset for pagination

        Returns:
            List of post data
        """
        # This endpoint might not exist in new API, return empty list
        logger.warning("get_user_posts not implemented for new API")
        return []

    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from Binance Square.
        Note: Endpoint might be different in new API.

        Args:
            post_id: ID of the post to delete

        Returns:
            True if successful, False otherwise
        """
        logger.warning("delete_post not implemented for new API")
        return False

    async def get_square_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Binance Square usage.
        Note: Endpoint might not exist in new API.

        Returns:
            Statistics data
        """
        logger.warning("get_square_stats not implemented for new API")
        return {}