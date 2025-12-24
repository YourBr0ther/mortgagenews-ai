"""
Pushbullet notification service for newsletter delivery.
"""
import aiohttp
import logging
from typing import List
from src.models.article import ContentItem, Category

logger = logging.getLogger(__name__)

# Category labels for plain text
CATEGORY_LABELS = {
    Category.WORKFLOW: "WORKFLOW",
    Category.LEADS: "LEADS",
    Category.FILES: "FILES",
}


class PushbulletService:
    """Service for sending newsletters via Pushbullet."""

    API_URL = "https://api.pushbullet.com/v2/pushes"

    def __init__(self, config):
        self.api_key = config.PUSHBULLET_API_KEY

    async def send_newsletter(
        self,
        executive_summary: str,
        items: List[ContentItem],
        tldr: List[str],
        date_str: str
    ) -> bool:
        """
        Send the newsletter via Pushbullet.

        Args:
            executive_summary: The executive summary text
            items: List of top ContentItem objects
            tldr: List of TL;DR bullet points
            date_str: Formatted date string for the title

        Returns:
            True if successful, False otherwise
        """
        title = f"Mortgage AI Briefing - {date_str}"
        body = self._format_newsletter(executive_summary, items, tldr)

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

    def _format_newsletter(self, summary: str, items: List[ContentItem], tldr: List[str]) -> str:
        """Format the newsletter body with TL;DR and category grouping."""
        lines = [
            "MORTGAGE AI BRIEFING",
            "=" * 40,
            "",
            "⚡ TL;DR — 30 SECOND SCAN",
            "-" * 30,
        ]

        # Add TL;DR bullets
        for bullet in tldr:
            lines.append(f"• {bullet}")
        lines.append("")

        # Strategic summary
        lines.extend([
            "STRATEGIC SUMMARY",
            "-" * 30,
            summary,
            "",
            "=" * 40,
        ])

        # Group items by category
        grouped = {Category.WORKFLOW: [], Category.LEADS: [], Category.FILES: []}
        for item in items:
            cat = item.category or Category.WORKFLOW
            grouped[cat].append(item)

        # Format each category section
        for category in [Category.WORKFLOW, Category.LEADS, Category.FILES]:
            cat_items = grouped[category]
            if not cat_items:
                continue

            label = CATEGORY_LABELS[category]
            lines.append("")
            lines.append(f"⚙️ {label}" if category == Category.WORKFLOW else
                        f"📈 {label}" if category == Category.LEADS else
                        f"📄 {label}")
            lines.append("-" * 30)

            for item in cat_items:
                title = item.title[:70] + "..." if len(item.title) > 70 else item.title
                lines.append(f"\n{title}")
                lines.append(f"[{item.source}]")

                if item.summary:
                    sentences = self._split_sentences(item.summary)
                    for j, sentence in enumerate(sentences[:2]):
                        if sentence.strip():
                            prefix = ">" if j == 0 else "→"
                            lines.append(f"{prefix} {sentence.strip()}")

                lines.append(item.url)
                lines.append("")

        lines.append("=" * 40)
        lines.append("Curated for mortgage tech leaders")

        return "\n".join(lines)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        # Split on period, exclamation, or question mark followed by space
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if s.strip()]
