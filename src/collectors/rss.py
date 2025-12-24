"""
RSS feed collector for fintech and mortgage news.
"""
import feedparser
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from time import mktime
from src.collectors.base import BaseCollector
from src.models.article import ContentItem, SourceType


class RSSCollector(BaseCollector):
    """Collects articles from RSS feeds."""

    # Keywords to filter for mortgage/AI content
    KEYWORDS = [
        "mortgage", "ai", "artificial intelligence", "automation",
        "lending", "fintech", "underwriting", "loan", "machine learning",
        "proptech", "real estate tech", "housing"
    ]

    async def collect(self) -> List[ContentItem]:
        """Fetch and filter RSS feeds for relevant content."""
        items = []
        yesterday = datetime.now(timezone.utc) - timedelta(days=2)  # 2 days to catch more

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for feed_url in self.config.RSS_FEEDS:
                try:
                    async with session.get(feed_url) as resp:
                        if resp.status == 200:
                            content = await resp.text()
                            feed = feedparser.parse(content)

                            feed_title = feed.feed.get("title", feed_url)

                            for entry in feed.entries:
                                # Check if entry is recent and relevant
                                published = self._parse_date(entry)
                                if published and published >= yesterday:
                                    if self._is_relevant(entry):
                                        items.append(ContentItem(
                                            title=entry.get("title", "Untitled"),
                                            url=entry.get("link", ""),
                                            source=feed_title,
                                            source_type=SourceType.RSS,
                                            published_at=published,
                                            description=self._clean_description(
                                                entry.get("summary", "")
                                            )
                                        ))

                            self.logger.debug(f"Processed feed: {feed_title}")
                        else:
                            self.logger.warning(f"RSS feed {feed_url} returned {resp.status}")

                except aiohttp.ClientError as e:
                    self.logger.warning(f"RSS fetch failed for {feed_url}: {e}")
                except Exception as e:
                    self.logger.warning(f"RSS parse error for {feed_url}: {e}")

        self.logger.info(f"Collected {len(items)} articles from RSS feeds")
        return items

    def _is_relevant(self, entry) -> bool:
        """Check if entry contains mortgage/AI keywords."""
        text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
        return any(kw in text for kw in self.KEYWORDS)

    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse entry date from various formats."""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                timestamp = mktime(entry.published_parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                timestamp = mktime(entry.updated_parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception:
            pass
        return None

    def _clean_description(self, desc: str) -> str:
        """Clean and truncate description."""
        # Remove HTML tags (basic)
        import re
        clean = re.sub(r'<[^>]+>', '', desc)
        clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&')
        return clean[:500].strip()

    def get_source_name(self) -> str:
        return "RSS Feeds"
