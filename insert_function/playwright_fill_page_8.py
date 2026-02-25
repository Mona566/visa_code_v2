"""Page 8 Filler using Playwright"""
import time, logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

def fill_page_8(page: Page):
    logger.info("=" * 50)
    logger.info("Filling Page 8")
    logger.info("=" * 50)
    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)
        logger.info("Page 8 completed")
    except Exception as e:
        logger.warn(f"Error in page 8: {e}")
