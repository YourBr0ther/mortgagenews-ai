"""
Abstract base class for content collectors.
"""
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from src.models.article import ContentItem
    from src.config import Config


class BaseCollector(ABC):
    """Base class for all content collectors."""

    def __init__(self, config: "Config"):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def collect(self) -> List["ContentItem"]:
        """Collect content items from the source."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this source."""
        pass
