"""
GitHub trending repositories collector for mortgage AI projects.
Uses GitHub Search API (free: 10 requests/minute unauthenticated, 30 authenticated).
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
from src.collectors.base import BaseCollector
from src.models.article import ContentItem, SourceType


class GitHubCollector(BaseCollector):
    """Collects trending mortgage AI repositories from GitHub."""

    SEARCH_URL = "https://api.github.com/search/repositories"

    # Search queries for mortgage tech repos (principal engineer focus)
    QUERIES = [
        # Workflow & automation
        "mortgage automation",
        "loan origination system",
        "lending workflow",
        # Document processing
        "mortgage document OCR",
        "loan document extraction",
        "pdf extraction financial",
        # Lead generation & CRM
        "mortgage CRM",
        "lead scoring lending",
        # AI/ML for lending
        "underwriting machine learning",
        "credit decisioning AI"
    ]

    async def collect(self) -> List[ContentItem]:
        """Search for trending mortgage AI repositories."""
        # Look for repos updated in the last 7 days
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        items = []
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MortgageAINewsletter/1.0"
        }

        if self.config.GITHUB_TOKEN:
            headers["Authorization"] = f"token {self.config.GITHUB_TOKEN}"

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for query in self.QUERIES:
                try:
                    params = {
                        "q": f"{query} pushed:>{week_ago}",
                        "sort": "updated",
                        "order": "desc",
                        "per_page": 5
                    }

                    async with session.get(
                        self.SEARCH_URL,
                        params=params,
                        headers=headers
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for repo in data.get("items", []):
                                try:
                                    updated_at = datetime.fromisoformat(
                                        repo["updated_at"].replace("Z", "+00:00")
                                    )

                                    # Create descriptive title
                                    stars = repo.get("stargazers_count", 0)
                                    title = f"[GitHub] {repo['full_name']}"
                                    if stars > 0:
                                        title += f" ({stars} stars)"

                                    items.append(ContentItem(
                                        title=title,
                                        url=repo["html_url"],
                                        source="GitHub",
                                        source_type=SourceType.GITHUB,
                                        published_at=updated_at,
                                        description=repo.get("description", "")[:500] if repo.get("description") else ""
                                    ))
                                except Exception as e:
                                    self.logger.warning(f"Failed to parse repo: {e}")

                        elif resp.status == 403:
                            self.logger.warning("GitHub rate limit hit, waiting...")
                            await asyncio.sleep(60)
                        else:
                            self.logger.warning(f"GitHub search returned {resp.status}")

                except aiohttp.ClientError as e:
                    self.logger.warning(f"GitHub search failed for '{query}': {e}")
                except Exception as e:
                    self.logger.warning(f"GitHub search error for '{query}': {e}")

                # Rate limit: wait between queries
                await asyncio.sleep(2)

        # Deduplicate by URL
        seen = set()
        unique_items = []
        for item in items:
            if item.url not in seen:
                seen.add(item.url)
                unique_items.append(item)

        self.logger.info(f"Collected {len(unique_items)} repositories from GitHub")
        return unique_items

    def get_source_name(self) -> str:
        return "GitHub"
