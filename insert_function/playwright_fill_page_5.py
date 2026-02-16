"""Page 5 Filler using Playwright"""
import time, logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

def fill_page_5(page: Page):
    logger.info("=" * 50)
    logger.info("Filling Page 5")
    logger.info("=" * 50)
    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        logger.info("Page 5 completed")
    except Exception as e:
        logger.warn(f"Error in page 5: {e}")
