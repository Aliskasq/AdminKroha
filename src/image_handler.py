"""
Image handling for Telegram Binance Bot.

This module handles image downloading, processing, and uploading for posts.
"""

import base64
import io
import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import hashlib
from datetime import datetime

from .config import Config

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
            if image.size != self.max_image_size:
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
        Upload processed image to Binance Square.

        Args:
            image_data: Processed image data
            filename: Optional filename

        Returns:
            Upload response with image URL
        """
        # Process the image
        processed = await self.process_image(image_data)

        # Prepare upload data
        upload_data = {
            'image': base64.b64encode(processed['data']).decode('utf-8'),
            'contentType': processed['mime_type'],
            'filename': filename or f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            'size': len(processed['data']),
            'hash': processed['hash'],
            'dimensions': {
                'width': processed['size'][0],
                'height': processed['size'][1]
            }
        }

        # Note: This would be implemented with actual Binance API call
        # For now, returning mock response
        mock_response = {
            'url': f"https://www.binance.com/square/images/{upload_data['hash']}.{upload_data['filename'].split('.')[-1]}",
            'id': f"img_{upload_data['hash'][:8]}",
            'uploadTime': datetime.now().isoformat(),
            'size': upload_data['size'],
            'format': upload_data['filename'].split('.')[-1].upper()
        }

        logger.info(f"Image uploaded successfully: {mock_response['url']}")
        return mock_response

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