"""
Data models for collected content items.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class SourceType(Enum):
    """Type of content source."""
    NEWS_API = "newsapi"
    RSS = "rss"
    GITHUB = "github"


@dataclass
class ContentItem:
    """Represents a news article or GitHub repository."""

    title: str
    url: str
    source: str
    source_type: SourceType
    published_at: datetime
    description: Optional[str] = None
    summary: Optional[str] = None  # LLM-generated summary
    relevance_score: float = 0.0  # LLM-assigned score

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "source_type": self.source_type.value,
            "published_at": self.published_at.isoformat(),
            "description": self.description,
            "summary": self.summary,
            "relevance_score": self.relevance_score
        }

    def __str__(self) -> str:
        return f"{self.title} ({self.source})"
