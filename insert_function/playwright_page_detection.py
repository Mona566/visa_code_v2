"""
Page Detection for Playwright

Detects current page state and handles redirects/errors.
"""

import logging
import time
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


def detect_current_page_state(page: Page) -> str:
    """
    Detect the current page state based on URL.

    Args:
        page: Playwright page object

    Returns:
        str: Page identifier (e.g., 'homepage', 'privacy', 'form_page_1', etc.)
    """
    url = page.url

    if "OnlineHome.aspx" in url and "OnlineHome2" not in url:
        return "homepage"
    elif "OnlineHome2.aspx" in url:
        return "privacy_page"
    elif "VisaTypeDetails.aspx" in url:
        return "form_page_1"
    elif "GeneralApplicantInfo.aspx" in url:
        return "form_page_2"
    elif "PassportDetails.aspx" in url:
        return "form_page_3"
    elif "ErrorPage" in url or "error" in url.lower():
        return "error_page"
    else:
        return "unknown"


def check_for_error_page(page: Page) -> bool:
    """
    Check if the current page is an error page.

    Args:
        page: Playwright page object

    Returns:
        bool: True if error page detected
    """
    try:
        # Check for error indicators in URL
        if "ErrorPage" in page.url or "error" in page.url.lower():
            return True

        # Check for error text on page
        error_text = page.get_by_text("Error", exact=False)
        if error_text.count() > 0:
            logger.warning("Error page detected")
            return True

        return False

    except Exception as e:
        logger.error(f"Error checking for error page: {e}")
        return False


def handle_intermediate_page(page: Page) -> bool:
    """
    Handle any intermediate pages (e.g., loading, redirecting).

    Args:
        page: Playwright page object

    Returns:
        bool: True if intermediate page was handled
    """
    try:
        # Wait for any loading to complete
        page.wait_for_load_state("networkidle", timeout=5000)

        # Check if we're still on an intermediate page
        url = page.url

        if "Loading" in url or "Redirect" in url:
            logger.info("Detected intermediate page, waiting...")
            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=10000)
            return True

        return False

    except PlaywrightTimeoutError:
        logger.warn("Timeout waiting for intermediate page to load")
        return False
    except Exception as e:
        logger.error(f"Error handling intermediate page: {e}")
        return False


def wait_for_postback_complete(page: Page, timeout: int = 30000):
    """
    Wait for ASP.NET PostBack to complete.

    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    """
    try:
        # Wait for network to be idle (AJAX complete)
        page.wait_for_load_state("networkidle", timeout=timeout)
        time.sleep(0.5)
    except PlaywrightTimeoutError:
        logger.warn("PostBack wait timeout, continuing...")
    except Exception as e:
        logger.error(f"Error waiting for postback: {e}")


def is_page_ready(page: Page) -> bool:
    """
    Check if the page is ready for interaction.

    Args:
        page: Playwright page object

    Returns:
        bool: True if page is ready
    """
    try:
        # Check document ready state
        ready = page.evaluate("document.readyState")
        return ready == "complete"
    except Exception:
        return False
