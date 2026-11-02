"""
Image handling for Telegram Binance Bot.

This module handles image downloading, processing, and uploading for posts.
Uses Binance Square OpenAPI v2 for real image upload (4-step flow).
"""

import asyncio
import base64
import io
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

import aiohttp

from .config import Config
from .binance_api import BinanceSquareAPI

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles image processing and uploading for Telegram posts."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize image handler.

        Args:
            config: Bot configuration
        """
        self.config = config or Config.load_from_env()
        self.supported_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
        self.max_image_size = (1920, 1080)  # Maximum image dimensions
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.binance_api: Optional[BinanceSquareAPI] = None

    def set_binance_api(self, binance_api: BinanceSquareAPI):
        """Set the Binance API client for uploads."""
        self.binance_api = binance_api

    async def process_image(
        self,
        image_data: bytes,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process image for posting to Binance Square.

        Args:
            image_data: Raw image data
            options: Processing options

        Returns:
            Processed image data and metadata
        """
        try:
            # Validate image size
            if len(image_data) > self.max_file_size:
                raise ValueError(f"Image size exceeds limit: {len(image_data)} bytes")

            # Open and validate image
            image = Image.open(io.BytesIO(image_data))

            # Check if format is supported
            if image.format not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {image.format}")

            # Resize image if necessary
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)

            # Add watermark if configured
            if options and options.get('add_watermark', False):
                image = self._add_watermark(image, options.get('watermark_text', 'Binance Square'))

            # Add metadata if configured
            if options and options.get('add_metadata', False):
                image = self._add_metadata(image, options)

            # Convert to bytes
            output = io.BytesIO()
            image.save(output, format=image.format)
            processed_data = output.getvalue()

            # Calculate hash
            image_hash = hashlib.sha256(processed_data).hexdigest()

            result = {
                'data': processed_data,
                'format': image.format,
                'size': image.size,
                'hash': image_hash,
                'mime_type': f'image/{image.format.lower()}'
            }

            logger.info(f"Image processed successfully: {image.format}, {image.size[0]}x{image.size[1]}")
            return result

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise

    async def upload_image(
        self,
        image_data: bytes,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload processed image to Binance Square using the 4-step v2 flow.

        Step 1: Get presigned URL
        Step 2: PUT image to presigned URL
        Step 3: Poll image status
        Step 4: Return image URL for use in post

        Args:
            image_data: Processed image data
            filename: Optional filename

        Returns:
            Dictionary with image URL
        """
        if not self.binance_api:
            raise RuntimeError("Binance API not set. Call set_binance_api() first.")

        if not filename:
            filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Ensure format is correct for filename
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        elif filename.lower().endswith('.webp'):
            content_type = 'image/webp'
        else:
            content_type = 'image/jpeg'
            filename = filename.rsplit('.', 1)[0] + '.jpg'

        try:
            # Step 1: Get presigned URL
            logger.info(f"Step 1: Getting presigned URL for {filename}")
            presigned_response = await self.binance_api._request(
                'POST',
                f'{self.binance_api.openapi_v2_url}/image/presignedUrl',
                data={'imageName': filename}
            )

            presigned_data = presigned_response.get('data', {})
            presigned_url = presigned_data.get('presignedUrl')
            file_ticket = presigned_data.get('fileTicket')

            if not presigned_url or not file_ticket:
                raise Exception(f"Failed to get presigned URL: {presigned_response}")

            logger.info(f"Got presigned URL, fileTicket: {file_ticket}")

            # Step 2: Upload image to presigned URL (PUT request)
            logger.info(f"Step 2: Uploading image to presigned URL")
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            async with aiohttp.ClientSession(timeout=timeout) as upload_session:
                async with upload_session.put(
                    presigned_url,
                    data=image_data,
                    headers={'Content-Type': content_type}
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"Image upload to presigned URL failed: HTTP {response.status} - {error_text}")

            logger.info(f"Image uploaded to presigned URL successfully")

            # Step 3: Poll image status
            logger.info(f"Step 3: Polling image status")
            image_url = await self._poll_image_status(file_ticket)
            if not image_url:
                raise Exception("Image processing timed out or failed")

            logger.info(f"Step 4: Image ready at {image_url}")
            return {'url': image_url}

        except Exception as e:
            logger.error(f"Failed to upload image to Binance: {e}")
            raise

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
        if not self.binance_api:
            raise RuntimeError("Binance API not set")

        for attempt in range(max_attempts):
            try:
                status_response = await self.binance_api._request(
                    'POST',
                    f'{self.binance_api.openapi_v2_url}/image/imageStatus',
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

    def _add_watermark(self, image: Image.Image, text: str) -> Image.Image:
        """
        Add watermark to image.

        Args:
            image: Image to add watermark to
            text: Watermark text

        Returns:
            Image with watermark
        """
        # Create a copy to avoid modifying the original
        img = image.copy()
        draw = ImageDraw.Draw(img)

        # Try to use a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        # Calculate text position
        text_width, text_height = draw.textsize(text, font)
        position = (img.width - text_width - 10, img.height - text_height - 10)

        # Add semi-transparent background
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 128))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.text(position, text, font=font, fill=(255, 255, 255, 255))

        # Composite the watermark
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

        return img

    def _add_metadata(self, image: Image.Image, options: Dict[str, Any]) -> Image.Image:
        """
        Add metadata to image.

        Args:
            image: Image to add metadata to
            options: Metadata options

        Returns:
            Image with metadata
        """
        # In a real implementation, this would add EXIF data or other metadata
        # For this example, we'll just log that metadata was added
        logger.info("Metadata would be added to image in production")
        return image

    async def validate_image_format(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Validate image format and properties.

        Args:
            image_data: Raw image data

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to open the image
            image = Image.open(io.BytesIO(image_data))

            # Check if format is supported
            if image.format not in self.supported_formats:
                return False, f"Unsupported image format: {image.format}"

            # Check if image size is acceptable
            if image.size[0] == 0 or image.size[1] == 0:
                return False, "Invalid image dimensions"

            # Check if file size is acceptable
            if len(image_data) > self.max_file_size:
                return False, f"Image size exceeds limit: {len(image_data)} bytes"

            return True, "Image is valid"

        except Exception as e:
            return False, f"Error validating image: {str(e)}"

    async def create_thumbnail(
        self,
        image_data: bytes,
        size: Tuple[int, int] = (300, 300)
    ) -> bytes:
        """
        Create thumbnail from image data.

        Args:
            image_data: Original image data
            size: Thumbnail size

        Returns:
            Thumbnail image data
        """
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG')
            thumbnail_data = output.getvalue()

            return thumbnail_data

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            raise

    async def compress_image(
        self,
        image_data: bytes,
        quality: int = 85
    ) -> bytes:
        """
        Compress image to reduce file size.

        Args:
            image_data: Original image data
            quality: Compression quality (1-100)

        Returns:
            Compressed image data
        """
        try:
            # Open the image
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Compress the image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality)
            compressed_data = output.getvalue()

            logger.info(f"Image compressed from {len(image_data)} to {len(compressed_data)} bytes")
            return compressed_data

        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise

    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """
        Get information about an image.

        Args:
            image_data: Image data

        Returns:
            Dictionary with image information
        """
        try:
            image = Image.open(io.BytesIO(image_data))

            info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'info': image.info,
                'file_size': len(image_data),
                'is_valid': True
            }

            return info

        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {
                'is_valid': False,
                'error': str(e)
            }