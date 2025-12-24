"""
Deduplication utilities for content items.
"""
from typing import List
from difflib import SequenceMatcher
from src.models.article import ContentItem


def deduplicate_items(items: List[ContentItem]) -> List[ContentItem]:
    """
    Remove duplicate items based on URL and title similarity.

    Args:
        items: List of ContentItem objects to deduplicate

    Returns:
        List of unique ContentItem objects
    """
    seen_urls = set()
    seen_titles = []
    unique = []

    for item in items:
        # Check exact URL match
        if item.url in seen_urls:
            continue

        # Check title similarity (>80% similar = duplicate)
        is_duplicate = False
        for seen_title in seen_titles:
            similarity = SequenceMatcher(
                None,
                item.title.lower(),
                seen_title.lower()
            ).ratio()
            if similarity > 0.8:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_urls.add(item.url)
            seen_titles.append(item.title)
            unique.append(item)

    return unique
