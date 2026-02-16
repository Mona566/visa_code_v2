"""
Playwright-based Browser Entry Point

Alternative to insert_browser.py using Playwright for human-like interaction.

Usage:
    conda run -n visa_autofill python playwright_insert_browser.py

With options:
    conda run -n visa_autofill python playwright_insert_browser.py --start-page 5 --headless
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from insert_function.playwright_main_flow import auto_fill_inis_form

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Playwright-based INIS Visa Form Filler"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="Page number to start from (1-10)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--screenshots",
        action="store_true",
        help="Enable screenshot capture"
    )
    parser.add_argument(
        "--screenshots-dir",
        type=str,
        default="screenshots_playwright",
        help="Directory for screenshots"
    )

    args = parser.parse_args()

    # Validate start page
    if args.start_page < 1 or args.start_page > 10:
        logger.error("Start page must be between 1 and 10")
        return

    logger.info(f"Starting from page {args.start_page}")
    logger.info(f"Headless mode: {args.headless}")

    # Run the form filler
    browser = auto_fill_inis_form(
        start_page=args.start_page,
        headless=args.headless
    )

    # Note: browser stays open for user inspection
    # User should close it manually or press Ctrl+C


if __name__ == "__main__":
    main()
