"""
Configuration management using environment variables.
"""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # NewsAPI
    NEWSAPI_KEY: str = ""
    NEWSAPI_QUERY: str = "mortgage AI OR mortgage automation OR mortgage fintech OR lending AI"

    # NanoGPT
    NANOGPT_API_KEY: str = ""
    NANOGPT_BASE_URL: str = "https://nano-gpt.com/api/v1"
    NANOGPT_MODEL: str = "gpt-4o-mini"

    # Pushbullet
    PUSHBULLET_API_KEY: str = ""

    # GitHub
    GITHUB_TOKEN: str = ""

    # RSS Feeds
    RSS_FEEDS: List[str] = field(default_factory=list)

    # Application
    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "America/New_York"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        default_feeds = [
            "https://www.finextra.com/rss/headlines.aspx",
            "https://www.housingwire.com/feed/",
            "https://www.pymnts.com/feed/"
        ]

        rss_feeds_env = os.getenv("RSS_FEEDS", "")
        rss_feeds = rss_feeds_env.split(",") if rss_feeds_env else default_feeds

        return cls(
            NEWSAPI_KEY=os.environ.get("NEWSAPI_KEY", ""),
            NEWSAPI_QUERY=os.getenv(
                "NEWSAPI_QUERY",
                "mortgage AI OR mortgage automation OR mortgage fintech OR lending AI"
            ),
            NANOGPT_API_KEY=os.environ.get("NANOGPT_API_KEY", ""),
            NANOGPT_BASE_URL=os.getenv("NANOGPT_BASE_URL", "https://nano-gpt.com/api/v1"),
            NANOGPT_MODEL=os.getenv("NANOGPT_MODEL", "gpt-4o-mini"),
            PUSHBULLET_API_KEY=os.environ.get("PUSHBULLET_API_KEY", ""),
            GITHUB_TOKEN=os.getenv("GITHUB_TOKEN", ""),
            RSS_FEEDS=rss_feeds,
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            TIMEZONE=os.getenv("TIMEZONE", "America/New_York")
        )

    def validate(self) -> List[str]:
        """Validate required configuration. Returns list of missing keys."""
        missing = []
        if not self.NEWSAPI_KEY:
            missing.append("NEWSAPI_KEY")
        if not self.NANOGPT_API_KEY:
            missing.append("NANOGPT_API_KEY")
        if not self.PUSHBULLET_API_KEY:
            missing.append("PUSHBULLET_API_KEY")
        return missing
