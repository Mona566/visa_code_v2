"""Page 6 Filler using Playwright"""
import time, logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

def fill_page_6(page: Page):
    logger.info("=" * 50)
    logger.info("Filling Page 6")
    logger.info("=" * 50)
    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        logger.info("Page 6 completed")
    except Exception as e:
        logger.warn(f"Error in page 6: {e}")
