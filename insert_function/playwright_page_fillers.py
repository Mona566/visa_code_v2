"""
Page Dispatcher for Playwright

Routes to the correct page filler based on current URL.
"""

import logging
from playwright.sync_api import Page

from .playwright_fill_page_1 import fill_page_1
from .playwright_fill_page_2 import fill_page_2
from .playwright_fill_page_3 import fill_page_3
from .playwright_fill_page_4 import fill_page_4
from .playwright_fill_page_5 import fill_page_5
from .playwright_fill_page_6 import fill_page_6
from .playwright_fill_page_7 import fill_page_7
from .playwright_fill_page_8 import fill_page_8
from .playwright_fill_page_9 import fill_page_9
from .playwright_fill_page_10 import fill_page_10

logger = logging.getLogger(__name__)


def dispatch_to_page(page: Page, page_number: int = None):
    """
    Dispatch to the appropriate page filler.

    Args:
        page: Playwright page object
        page_number: Specific page number to fill (1-10).
                    If None, auto-detects from URL.

    Returns:
        int: The page number that was filled
    """
    if page_number is None:
        page_number = detect_page_from_url(page.url)

    logger.info(f"Dispatching to page {page_number}")

    # Map page numbers to filler functions
    page_fillers = {
        1: fill_page_1,
        2: fill_page_2,
        3: fill_page_3,
        4: fill_page_4,
        5: fill_page_5,
        6: fill_page_6,
        7: fill_page_7,
        8: fill_page_8,
        9: fill_page_9,
        10: fill_page_10,
    }

    filler = page_fillers.get(page_number)
    if filler:
        filler(page)
    else:
        logger.warning(f"No filler for page {page_number}")

    return page_number


def detect_page_from_url(url: str) -> int:
    """
    Detect which page we're on based on URL.

    Args:
        url: Current page URL

    Returns:
        int: Page number (1-10)
    """
    if "VisaTypeDetails.aspx" in url:
        return 1
    elif "GeneralApplicantInfo.aspx" in url:
        return 2
    elif "PassportDetails.aspx" in url:
        return 3
    elif "Page3" in url:
        return 3
    elif "Page4" in url:
        return 4
    elif "Page5" in url:
        return 5
    elif "Page6" in url:
        return 6
    elif "Page7" in url:
        return 7
    elif "Page8" in url:
        return 8
    elif "Page9" in url:
        return 9
    elif "Page10" in url or "Declaration" in url:
        return 10
    else:
        # Default to page 1
        return 1
