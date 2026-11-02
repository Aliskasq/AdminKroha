"""
Content generation and formatting for Telegram Binance Bot.

This module handles content generation, formatting, and enhancement
for posts to Binance Square.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from .config import Config


class ContentGenerator:
    """Generates and formats content for Binance Square posts."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize content generator.

        Args:
            config: Bot configuration
        """
        self.config = config or Config.load_from_env()
        self.hashtag_pattern = re.compile(r'#\w+')
        self.mention_pattern = re.compile(r'@\w+')
        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.ticker_pattern = re.compile(r'\$?\d+\.?\d*\s*[A-Z]{3,10}')

    def generate_content(
        self,
        content: str,
        post_type: str = 'text',
        image_url: Optional[str] = None,
        add_hashtags: bool = True,
        add_ticker_analysis: bool = False
    ) -> str:
        """
        Generate content for posting to Binance Square.

        Args:
            content: Base content text
            post_type: Type of post
            image_url: URL of associated image
            add_hashtags: Whether to add relevant hashtags
            add_ticker_analysis: Whether to add ticker analysis

        Returns:
            Formatted content string
        """
        # Start with base content - preserve user content exactly as per Binance API guidelines
        formatted_content = content.strip()

        # Preserve empty lines (paragraph breaks) by adding zero-width space
        # Binance Square collapses empty lines, so we add zero-width space to preserve them
        formatted_content = self._preserve_empty_lines(formatted_content)

        # Do NOT add image URL to text - Binance API handles images via imageList parameter
        # Add ticker analysis if explicitly enabled
        if add_ticker_analysis:
            tickers = self._extract_tickers(content)
            if tickers:
                analysis = self._generate_ticker_analysis(tickers)
                formatted_content += f"\n\n📊 {analysis}"

        # Do NOT add hashtags automatically - user provides them in content
        # Do NOT add timestamp - Binance handles post time

        return formatted_content

    def _preserve_empty_lines(self, text: str) -> str:
        """
        Preserve empty lines (paragraph breaks) by adding zero-width space.
        Binance Square collapses consecutive newlines, so we add
        zero-width space (U+200B) to lines that would otherwise be empty.

        Args:
            text: Input text with potential empty lines

        Returns:
            Text with zero-width spaces added to empty lines
        """
        lines = text.split('\n')
        preserved_lines = []
        for line in lines:
            if line.strip() == '':
                # Empty line - add zero-width space to preserve it
                preserved_lines.append('​')
            else:
                preserved_lines.append(line)
        return '\n'.join(preserved_lines)

    def _extract_and_format_hashtags(self, content: str) -> str:
        """
        Extract and format relevant hashtags from content.

        Args:
            content: Content text

        Returns:
            Formatted hashtags string
        """
        # Extract hashtags from content
        hashtags = self.hashtag_pattern.findall(content)

        # Add trending hashtags if none found
        if not hashtags:
            hashtags = self.config.allowed_hashtags_list

        # Format hashtags
        formatted = " ".join(f"#{tag}" for tag in hashtags[:5])  # Limit to 5 hashtags

        return f"\n\nTags: {formatted}"

    def _extract_tickers(self, content: str) -> List[str]:
        """
        Extract cryptocurrency tickers from content.

        Args:
            content: Content text

        Returns:
            List of ticker symbols
        """
        # Common ticker patterns
        ticker_patterns = [
            r'\b(BTC|ETH|ADA|DOT|SOL|AVAX|BNB|MATIC|ADA|LINK|UNI|AAVE|SNX|YFI|KNC|SNT|RPN|BAND|MKR|REN|LRC|ZRX)\b',
            r'\b(BTCUSDT|ETHUSDT|ADAUSDT|DOTUSDT|SOLUSDT|AVAXUSDT|BNBUSDT|MATICUSDT|LINKUSDT|UNIUSDT|AAVEUSDT|SNXUSDT|YFIUSDT|KNCUSDT|SNTUSDT|RPNUSDT|BANDUSDT|MKRUSDT|RENUSDT|LRCUSDT|ZRXUSDT)\b'
        ]

        tickers = []
        for pattern in ticker_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tickers.extend([match.upper() for match in matches if match])

        # Remove duplicates and return
        return list(set(tickers))

    def _generate_ticker_analysis(self, tickers: List[str]) -> str:
        """
        Generate ticker analysis text.

        Args:
            tickers: List of ticker symbols

        Returns:
            Formatted analysis text
        """
        analysis_parts = []

        for ticker in tickers[:3]:  # Limit to 3 tickers
            if ticker.endswith('USDT'):
                symbol = ticker[:-4]
            else:
                symbol = ticker

            # Mock ticker data (in real implementation, this would call Binance API)
            price = self._mock_ticker_price(symbol)
            change = self._mock_ticker_change(symbol)

            change_indicator = "📈" if change >= 0 else "📉"
            change_color = "green" if change >= 0 else "red"

            analysis_parts.append(
                f"{change_indicator} {symbol}: ${price:,.2f} ({change:+.2f}%) [{change_color}]"
            )

        return " | ".join(analysis_parts)

    def _mock_ticker_price(self, symbol: str) -> float:
        """
        Mock ticker price for demonstration.

        Args:
            symbol: Ticker symbol

        Returns:
            Mock price
        """
        prices = {
            'BTC': 45000.00,
            'ETH': 2300.00,
            'ADA': 0.85,
            'DOT': 42.00,
            'SOL': 95.00,
            'AVAX': 65.00,
            'BNB': 320.00,
            'MATIC': 1.10,
            'LINK': 25.00,
            'UNI': 8.50,
        }

        return prices.get(symbol.upper(), 100.0)

    def _mock_ticker_change(self, symbol: str) -> float:
        """
        Mock ticker change for demonstration.

        Args:
            symbol: Ticker symbol

        Returns:
            Mock percentage change
        """
        import random
        return random.uniform(-5, 5)

    def format_poll_content(
        self,
        question: str,
        options: List[str],
        add_analytics: bool = True
    ) -> str:
        """
        Format poll content for posting.

        Args:
            question: Poll question
            options: List of poll options
            add_analytics: Whether to add analytics

        Returns:
            Formatted poll content
        """
        content = f"🗳️ Poll: {question}\n\n"

        for i, option in enumerate(options, 1):
            content += f"{i}. {option}\n"

        if add_analytics:
            content += f"\n📊 Analytics: 0 votes | 0% participation"

        return content

    def format_error_message(self, error: str, context: Optional[str] = None) -> str:
        """
        Format error message for user display.

        Args:
            error: Error message
            context: Context information

        Returns:
            Formatted error message
        """
        message = f"❌ Error: {error}"

        if context:
            message += f"\n📝 Context: {context}"

        message += "\n\nPlease try again or use /help for more information."

        return message

    def format_success_message(self, action: str, details: Optional[str] = None) -> str:
        """
        Format success message for user display.

        Args:
            action: Action that was performed
            details: Additional details

        Returns:
            Formatted success message
        """
        message = f"✅ {action} completed successfully!"

        if details:
            message += f"\n📝 {details}"

        return message

    def detect_content_type(self, content: str) -> str:
        """
        Detect content type based on content characteristics.

        Args:
            content: Content text

        Returns:
            Detected content type
        """
        # Check for image indicators
        if any(word in content.lower() for word in ['image', 'photo', 'picture', 'img', '📸']):
            return 'image'

        # Check for link indicators
        if self.url_pattern.search(content):
            return 'article'

        # Check for poll indicators
        if any(word in content.lower() for word in ['poll', 'vote', 'option', 'choice', '🗳️']):
            return 'poll'

        # Default to text
        return 'text'