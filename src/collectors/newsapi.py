"""
NewsAPI.org collector for mortgage AI news.
Free tier: 100 requests/day.
"""
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import List
from src.collectors.base import BaseCollector
from src.models.article import ContentItem, SourceType


class NewsAPICollector(BaseCollector):
    """Collects news articles from NewsAPI.org."""

    BASE_URL = "https://newsapi.org/v2/everything"

    async def collect(self) -> List[ContentItem]:
        """Fetch articles from NewsAPI for the previous day."""
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        params = {
            "q": self.config.NEWSAPI_QUERY,
            "from": yesterday,
            "to": today,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 25,
            "apiKey": self.config.NEWSAPI_KEY
        }

        items = []
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.BASE_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for article in data.get("articles", []):
                            try:
                                # Parse published date
                                pub_str = article.get("publishedAt", "")
                                if pub_str:
                                    published_at = datetime.fromisoformat(
                                        pub_str.replace("Z", "+00:00")
                                    )
                                else:
                                    published_at = datetime.now(timezone.utc)

                                items.append(ContentItem(
                                    title=article.get("title", "Untitled"),
                                    url=article.get("url", ""),
                                    source=article.get("source", {}).get("name", "Unknown"),
                                    source_type=SourceType.NEWS_API,
                                    published_at=published_at,
                                    description=article.get("description", "")[:500] if article.get("description") else ""
                                ))
                            except Exception as e:
                                self.logger.warning(f"Failed to parse article: {e}")
                                continue

                        self.logger.info(f"Collected {len(items)} articles from NewsAPI")
                    elif resp.status == 401:
                        self.logger.error("NewsAPI authentication failed - check API key")
                    elif resp.status == 429:
                        self.logger.warning("NewsAPI rate limit exceeded")
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"NewsAPI error {resp.status}: {error_text[:200]}")

        except aiohttp.ClientError as e:
            self.logger.error(f"NewsAPI connection error: {e}")
        except Exception as e:
            self.logger.error(f"NewsAPI collection failed: {e}")

        return items

    def get_source_name(self) -> str:
        return "NewsAPI"
