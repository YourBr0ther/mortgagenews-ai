"""
Main orchestrator for the Mortgage AI Newsletter.
Coordinates data collection, analysis, and delivery.
"""
import asyncio
import logging
import sys
from datetime import datetime
import pytz

from src.config import Config
from src.collectors.newsapi import NewsAPICollector
from src.collectors.rss import RSSCollector
from src.collectors.github import GitHubCollector
from src.services.llm import NanoGPTService
from src.services.pushbullet import PushbulletService
from src.services.email import EmailService
from src.utils.logger import setup_logging
from src.utils.dedup import deduplicate_items


async def main():
    """Main entry point for the newsletter generation."""
    # Load configuration
    config = Config.from_env()

    # Setup logging
    setup_logging(config.LOG_LEVEL)
    logger = logging.getLogger("main")

    # Validate configuration
    missing = config.validate()
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        sys.exit(1)

    # Get current date in configured timezone
    tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(tz)
    date_str = now.strftime("%B %d, %Y")

    logger.info("=" * 50)
    logger.info(f"Mortgage AI Newsletter - {date_str}")
    logger.info("=" * 50)

    try:
        # Step 1: Collect content from all sources
        logger.info("Step 1: Collecting content from sources...")

        collectors = [
            NewsAPICollector(config),
            RSSCollector(config),
            GitHubCollector(config)
        ]

        all_items = []
        for collector in collectors:
            try:
                items = await collector.collect()
                logger.info(f"  - {collector.get_source_name()}: {len(items)} items")
                all_items.extend(items)
            except Exception as e:
                logger.error(f"  - {collector.get_source_name()}: FAILED - {e}")

        if not all_items:
            logger.warning("No content collected from any source. Exiting.")
            return

        logger.info(f"Total collected: {len(all_items)} items")

        # Step 2: Deduplicate
        logger.info("Step 2: Deduplicating items...")
        unique_items = deduplicate_items(all_items)
        logger.info(f"After deduplication: {len(unique_items)} items")

        if not unique_items:
            logger.warning("No unique items after deduplication. Exiting.")
            return

        # Step 3: Analyze and rank with LLM
        logger.info("Step 3: Analyzing content with NanoGPT...")
        llm_service = NanoGPTService(config)
        top_items = await llm_service.analyze_and_rank(unique_items)

        if not top_items:
            logger.warning("LLM analysis returned no items. Exiting.")
            return

        logger.info(f"Selected top {len(top_items)} items:")
        for i, item in enumerate(top_items, 1):
            logger.info(f"  {i}. {item.title[:60]}...")

        # Step 4: Generate executive summary
        logger.info("Step 4: Generating executive summary...")
        executive_summary = await llm_service.generate_executive_summary(top_items)
        logger.info(f"Summary: {executive_summary[:100]}...")

        # Step 5: Send newsletter
        logger.info("Step 5: Delivering newsletter...")

        success = False

        # Email delivery (primary)
        if config.has_email():
            logger.info("  - Sending via email...")
            email_service = EmailService(config)
            if email_service.send_newsletter(executive_summary, top_items, date_str):
                logger.info(f"  - Email sent to {config.EMAIL_TO}")
                success = True
            else:
                logger.error("  - Email delivery failed")

        # Pushbullet delivery (secondary/backup)
        if config.has_pushbullet():
            logger.info("  - Sending via Pushbullet...")
            pushbullet = PushbulletService(config)
            if await pushbullet.send_newsletter(executive_summary, top_items, date_str):
                logger.info("  - Pushbullet notification sent")
                success = True
            else:
                logger.error("  - Pushbullet delivery failed")

        if success:
            logger.info("=" * 50)
            logger.info("Newsletter delivered successfully!")
            logger.info("=" * 50)
        else:
            logger.error("All delivery methods failed")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Newsletter generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
