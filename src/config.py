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
    NEWSAPI_QUERY: str = "(mortgage OR lending OR loan) AND (AI OR automation OR OCR OR workflow OR lead generation OR document processing)"

    # NanoGPT
    NANOGPT_API_KEY: str = ""
    NANOGPT_BASE_URL: str = "https://nano-gpt.com/api/v1"
    NANOGPT_MODEL: str = "gpt-4o-mini"

    # Pushbullet (optional)
    PUSHBULLET_API_KEY: str = ""

    # Email Delivery
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""
    GMAIL_APP_PASSWORD: str = ""  # For Gmail SMTP
    SENDGRID_API_KEY: str = ""    # For SendGrid (alternative)

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
                "(mortgage OR lending OR loan) AND (AI OR automation OR OCR OR workflow OR lead generation OR document processing)"
            ),
            NANOGPT_API_KEY=os.environ.get("NANOGPT_API_KEY", ""),
            NANOGPT_BASE_URL=os.getenv("NANOGPT_BASE_URL", "https://nano-gpt.com/api/v1"),
            NANOGPT_MODEL=os.getenv("NANOGPT_MODEL", "gpt-4o-mini"),
            PUSHBULLET_API_KEY=os.environ.get("PUSHBULLET_API_KEY", ""),
            EMAIL_FROM=os.environ.get("EMAIL_FROM", ""),
            EMAIL_TO=os.environ.get("EMAIL_TO", ""),
            GMAIL_APP_PASSWORD=os.environ.get("GMAIL_APP_PASSWORD", ""),
            SENDGRID_API_KEY=os.environ.get("SENDGRID_API_KEY", ""),
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
        # Require at least one delivery method
        if not self.has_email() and not self.has_pushbullet():
            missing.append("Email (GMAIL_APP_PASSWORD or SENDGRID_API_KEY) or PUSHBULLET_API_KEY")
        return missing

    def has_email(self) -> bool:
        """Check if email delivery is configured (Gmail or SendGrid)."""
        has_gmail = bool(self.GMAIL_APP_PASSWORD and self.EMAIL_FROM and self.EMAIL_TO)
        has_sendgrid = bool(self.SENDGRID_API_KEY and self.EMAIL_FROM and self.EMAIL_TO)
        return has_gmail or has_sendgrid

    def has_pushbullet(self) -> bool:
        """Check if Pushbullet delivery is configured."""
        return bool(self.PUSHBULLET_API_KEY)
