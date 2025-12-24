"""
Pushbullet notification service for newsletter delivery.
"""
import aiohttp
import logging
from typing import List
from src.models.article import ContentItem

logger = logging.getLogger(__name__)


class PushbulletService:
    """Service for sending newsletters via Pushbullet."""

    API_URL = "https://api.pushbullet.com/v2/pushes"

    def __init__(self, config):
        self.api_key = config.PUSHBULLET_API_KEY

    async def send_newsletter(
        self,
        executive_summary: str,
        items: List[ContentItem],
        date_str: str
    ) -> bool:
        """
        Send the newsletter via Pushbullet.

        Args:
            executive_summary: The executive summary text
            items: List of top ContentItem objects
            date_str: Formatted date string for the title

        Returns:
            True if successful, False otherwise
        """
        title = f"Mortgage AI Daily - {date_str}"
        body = self._format_newsletter(executive_summary, items)

        headers = {
            "Access-Token": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "type": "note",
            "title": title,
            "body": body
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.API_URL,
                    json=payload,
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        logger.info("Newsletter sent successfully via Pushbullet")
                        return True
                    elif resp.status == 401:
                        logger.error("Pushbullet authentication failed - check API key")
                    elif resp.status == 429:
                        logger.error("Pushbullet rate limit exceeded (500 pushes/month)")
                    else:
                        error = await resp.text()
                        logger.error(f"Pushbullet error {resp.status}: {error[:200]}")
                    return False

        except aiohttp.ClientError as e:
            logger.error(f"Pushbullet connection error: {e}")
        except Exception as e:
            logger.error(f"Failed to send newsletter: {e}")

        return False

    def _format_newsletter(self, summary: str, items: List[ContentItem]) -> str:
        """Format the newsletter body for a Principal Engineer."""
        lines = [
            "STRATEGIC BRIEFING",
            "=" * 30,
            "",
            summary,
            "",
            "=" * 30,
            "TOP 5 ACTIONABLE ITEMS",
            "(Workflow | Leads | Clean Files)",
            "=" * 30,
            ""
        ]

        for i, item in enumerate(items, 1):
            # Clean up title
            title = item.title
            if len(title) > 70:
                title = title[:67] + "..."

            lines.append(f"{i}. {title}")
            lines.append(f"   [{item.source}]")
            lines.append("")

            # Summary as bullet points with actionable framing
            if item.summary:
                sentences = self._split_sentences(item.summary)
                for j, sentence in enumerate(sentences[:2]):
                    if sentence.strip():
                        # First sentence = what, second = action
                        prefix = ">" if j == 0 else "ACTION:"
                        lines.append(f"   {prefix} {sentence.strip()}")
            elif item.description:
                lines.append(f"   > {item.description[:150]}...")

            lines.append("")
            lines.append(f"   {item.url}")
            lines.append("")
            lines.append("-" * 30)
            lines.append("")

        lines.append("Curated for mortgage tech leaders")

        return "\n".join(lines)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Split on period, exclamation, or question mark followed by space
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if s.strip()]
