"""
NanoGPT API integration for content analysis and summarization.
Uses OpenAI-compatible API at nano-gpt.com.
"""
import aiohttp
import json
import logging
from typing import List, Optional
from src.models.article import ContentItem

logger = logging.getLogger(__name__)


class NanoGPTService:
    """Service for analyzing and summarizing content using NanoGPT."""

    def __init__(self, config):
        self.config = config
        self.base_url = config.NANOGPT_BASE_URL
        self.api_key = config.NANOGPT_API_KEY
        self.model = config.NANOGPT_MODEL

    async def analyze_and_rank(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Analyze items and return top 5 ranked by innovation/relevance.
        Also generates 2-sentence summaries for each.
        """
        if not items:
            return []

        # Prepare content for LLM
        content_text = self._prepare_content(items)
        prompt = self._build_analysis_prompt(content_text)

        try:
            response = await self._call_api(prompt)
            ranked_items = self._parse_response(response, items)
            return ranked_items[:5]
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Fallback: return first 5 items with basic summaries
            for item in items[:5]:
                if not item.summary:
                    item.summary = item.description[:200] if item.description else "No description available."
            return items[:5]

    async def generate_executive_summary(self, items: List[ContentItem]) -> str:
        """Generate an executive summary of all items."""
        if not items:
            return "No significant mortgage AI developments to report today."

        content = "\n".join([
            f"- {item.title}: {item.summary or item.description or 'No details'}"
            for item in items
        ])

        prompt = f"""Based on these mortgage AI news items from yesterday, write a 2-3 sentence executive summary highlighting the key trends and innovations in the mortgage AI space:

{content}

Write a professional, concise executive summary (2-3 sentences only):"""

        try:
            return await self._call_api(prompt)
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return "Today's mortgage AI landscape shows continued innovation across automation, lending technology, and AI-driven underwriting solutions."

    def _prepare_content(self, items: List[ContentItem]) -> str:
        """Format items for LLM analysis."""
        lines = []
        for i, item in enumerate(items[:20], 1):  # Limit to 20 items to manage token usage
            lines.append(f"[{i}] {item.title}")
            lines.append(f"    Source: {item.source}")
            desc = item.description[:300] if item.description else "N/A"
            lines.append(f"    Description: {desc}")
            lines.append(f"    URL: {item.url}")
            lines.append("")
        return "\n".join(lines)

    def _build_analysis_prompt(self, content: str) -> str:
        """Build the analysis prompt for ranking and summarization."""
        return f"""You are a mortgage industry AI analyst. Analyze these news items and GitHub repositories about mortgage AI and fintech innovation.

CONTENT TO ANALYZE:
{content}

TASK:
1. Rank these items by innovation and relevance to mortgage AI technology
2. For each of the TOP 5 items, write exactly 2 sentences summarizing the key innovation
3. Focus on: AI/ML applications, automation breakthroughs, new fintech tools, regulatory tech, underwriting innovations

RESPONSE FORMAT (JSON only, no other text):
{{
  "ranked_items": [
    {{
      "index": 1,
      "summary": "First sentence about the innovation. Second sentence with key details.",
      "relevance_score": 0.95
    }},
    {{
      "index": 3,
      "summary": "First sentence. Second sentence.",
      "relevance_score": 0.88
    }}
  ]
}}

Return ONLY valid JSON. Include exactly 5 items. Use the original index numbers from the content above."""

    async def _call_api(self, prompt: str) -> str:
        """Call NanoGPT API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error = await resp.text()
                    raise Exception(f"API error {resp.status}: {error[:200]}")

    def _parse_response(self, response: str, items: List[ContentItem]) -> List[ContentItem]:
        """Parse LLM response and update items with summaries and scores."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            ranked_items = []

            for ranked in data.get("ranked_items", []):
                idx = ranked["index"] - 1  # Convert to 0-indexed
                if 0 <= idx < len(items):
                    item = items[idx]
                    item.summary = ranked.get("summary", item.description)
                    item.relevance_score = ranked.get("relevance_score", 0.5)
                    ranked_items.append(item)

            logger.info(f"Successfully parsed {len(ranked_items)} ranked items from LLM")
            return ranked_items

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")

        # Fallback: return first 5 items
        return items[:5]
