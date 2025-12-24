"""
NanoGPT API integration for content analysis and summarization.
Uses OpenAI-compatible API at nano-gpt.com.
"""
import aiohttp
import json
import logging
from typing import List, Optional
from src.models.article import ContentItem, Category

logger = logging.getLogger(__name__)


class NanoGPTService:
    """Service for analyzing and summarizing content using NanoGPT."""

    def __init__(self, config):
        self.config = config
        self.base_url = config.NANOGPT_BASE_URL
        self.api_key = config.NANOGPT_API_KEY
        self.model = config.NANOGPT_MODEL

    async def analyze_and_rank(self, items: List[ContentItem]) -> tuple[List[ContentItem], List[str]]:
        """
        Analyze items and return top 6 ranked by category and relevance.
        Also generates 2-sentence summaries and TL;DR bullets.

        Returns:
            Tuple of (ranked_items, tldr_bullets)
        """
        if not items:
            return [], []

        # Prepare content for LLM
        content_text = self._prepare_content(items)
        prompt = self._build_analysis_prompt(content_text)

        try:
            response = await self._call_api(prompt)
            ranked_items, tldr = self._parse_response(response, items)
            return ranked_items[:6], tldr
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Fallback: return first 6 items with basic summaries
            for item in items[:6]:
                if not item.summary:
                    item.summary = item.description[:200] if item.description else "No description available."
                item.category = Category.WORKFLOW  # Default
            return items[:6], ["Check the full list for details."]

    async def generate_executive_summary(self, items: List[ContentItem]) -> str:
        """Generate an executive summary of all items."""
        if not items:
            return "No significant mortgage AI developments to report today."

        content = "\n".join([
            f"- {item.title}: {item.summary or item.description or 'No details'}"
            for item in items
        ])

        prompt = f"""You are briefing a Principal Engineer at a mortgage company. Based on these items from yesterday, write a 2-3 sentence executive summary focused on:
- Workflow optimization opportunities
- Lead generation innovations for loan officers
- Document processing / cleaner file improvements

{content}

Write a strategic executive summary highlighting actionable opportunities (2-3 sentences only):"""

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
        return f"""You are a strategic technology advisor for a Principal Engineer at a mortgage company. Analyze these items and categorize them by:

- WORKFLOW: Process automation, integrations, efficiency, LOS improvements
- LEADS: Lead generation, CRM, marketing automation, loan officer tools
- FILES: Document processing, OCR, data extraction, compliance, verification

CONTENT TO ANALYZE:
{content}

TASK:
1. Select the TOP 6 most actionable items (aim for 2 per category if possible)
2. Assign each item to exactly ONE category: "workflow", "leads", or "files"
3. For each item, write exactly 2 sentences:
   - Sentence 1: What it is and why it matters
   - Sentence 2: Specific action or next step to consider
4. Also provide 3 TL;DR bullet points (one key insight per category)

RESPONSE FORMAT (JSON only, no other text):
{{
  "tldr": [
    "Workflow: One sentence key takeaway",
    "Leads: One sentence key takeaway",
    "Files: One sentence key takeaway"
  ],
  "ranked_items": [
    {{
      "index": 1,
      "category": "workflow",
      "summary": "What this is and why it matters. Specific action to consider.",
      "relevance_score": 0.95
    }},
    {{
      "index": 3,
      "category": "leads",
      "summary": "Description of the innovation. Implementation consideration.",
      "relevance_score": 0.88
    }}
  ]
}}

Return ONLY valid JSON. Include exactly 6 items. Use original index numbers."""

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

    def _parse_response(self, response: str, items: List[ContentItem]) -> tuple[List[ContentItem], List[str]]:
        """Parse LLM response and update items with summaries, scores, and categories."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            ranked_items = []

            # Parse TL;DR
            tldr = data.get("tldr", [])

            # Category mapping
            category_map = {
                "workflow": Category.WORKFLOW,
                "leads": Category.LEADS,
                "files": Category.FILES
            }

            for ranked in data.get("ranked_items", []):
                idx = ranked["index"] - 1  # Convert to 0-indexed
                if 0 <= idx < len(items):
                    item = items[idx]
                    item.summary = ranked.get("summary", item.description)
                    item.relevance_score = ranked.get("relevance_score", 0.5)
                    # Set category
                    cat_str = ranked.get("category", "workflow").lower()
                    item.category = category_map.get(cat_str, Category.WORKFLOW)
                    ranked_items.append(item)

            logger.info(f"Successfully parsed {len(ranked_items)} ranked items from LLM")
            return ranked_items, tldr

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response was: {response[:500]}")
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")

        # Fallback: return first 6 items
        return items[:6], []
