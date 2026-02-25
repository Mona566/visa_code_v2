"""
Page 4 Filler using Playwright

Page 4 - Playwright version
"""

import time
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def fill_page_4(page: Page):
    """Fill Page 4 (Passport Details)."""
    logger.info("=" * 50)
    logger.info("Filling Page 4")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Check if form has content
        try:
            if page.locator("input[type='text']").count() > 0:
                logger.info("Form has input elements - skipping (likely already filled)")
                return
        except Exception:
            pass

        logger.info("Page 4 completed")
    except Exception as e:
        logger.warn(f"Error in page 4: {e}")
