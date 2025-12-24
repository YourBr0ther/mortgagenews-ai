"""
Logging configuration for the application.
"""
import logging
import sys
import os
from datetime import datetime


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with timestamps and structured format."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler (optional, for debugging)
    log_dir = os.getenv("LOG_DIR", "/app/logs")
    if os.path.exists(log_dir):
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"newsletter_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler = None

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    if file_handler:
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("feedparser").setLevel(logging.WARNING)
