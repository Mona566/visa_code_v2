"""
Playwright-based Browser Entry Point

Alternative to insert_browser.py that uses Playwright for human-like interaction.
This replaces Selenium with Playwright's smart locators.

Usage:
    conda run -n visa_autofill python insert_browser_playwright.py
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from insert_function.browser import HybridBrowser
from insert_function import page_detection, application_management
from insert_function.page_fillers import (
    fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
    fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10
)

# Import Playwright helpers
from insert_function import playwright_helpers as ph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_form_session_playwright(page):
    """
    Navigate through the INIS homepage and privacy statement using Playwright.

    Args:
        page: Playwright page object

    Returns:
        bool: True if successfully reached form page
    """
    homepage_url = "https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx"

    try:
        # Navigate to homepage
        logger.info(f"Navigating to homepage: {homepage_url}")
        page.goto(homepage_url)
        page.wait_for_load_state("domcontentloaded")

        # Step 1: Click "Continue" on OnlineHome.aspx
        logger.info("Looking for Continue button...")

        try:
            # Try the apply now button (most reliable)
            page.get_by_role("button", name="Continue").click()
        except Exception:
            try:
                page.get_by_label("Continue").click()
            except Exception:
                page.get_by_text("Continue").click()

        logger.info("Clicked Continue, waiting for OnlineHome2.aspx...")

        # Wait for navigation
        page.wait_for_url("**/OnlineHome2.aspx", timeout=10000)
        page.wait_for_load_state("domcontentloaded")

        # Step 2: Privacy checkbox + submit on OnlineHome2.aspx
        logger.info("On OnlineHome2.aspx - looking for privacy checkbox...")

        try:
            # Try to find and check the privacy checkbox
            page.get_by_label("I acknowledge").check()
            logger.info("Privacy checkbox checked")
        except Exception:
            logger.warn("Privacy checkbox not found by label, trying other methods...")
            try:
                page.get_by_role("checkbox").check()
            except Exception:
                logger.warn("Could not find privacy checkbox")

        # Click submit/continue button
        logger.info("Looking for submit button...")

        try:
            page.get_by_role("button", name="Save and Continue").click()
        except Exception:
            try:
                page.get_by_role("button", name="Continue").click()
            except Exception:
                page.get_by_text("Save and Continue").click()

        # Wait for VisaTypeDetails.aspx
        page.wait_for_url("**/VisaTypeDetails.aspx", timeout=15000)
        logger.info("Successfully reached form page")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize form session: {e}")
        return False


def fill_application_form_playwright(page, enable_screenshots=False, screenshots_dir="screenshots"):
    """
    Fill the application form using Playwright.

    Args:
        page: Playwright page object
        enable_screenshots: Whether to take screenshots
        screenshots_dir: Directory for screenshots
    """
    import time

    # Wait for page to be ready
    page.wait_for_load_state("domcontentloaded")
    time.sleep(2)

    # Determine which page we're on and fill accordingly
    current_url = page.url
    logger.info(f"Current URL: {current_url}")

    if "VisaTypeDetails.aspx" in current_url:
        logger.info("On VisaTypeDetails.aspx (Page 1)")
        if enable_screenshots:
            page.screenshot(path=f"{screenshots_dir}/page1_before.png")
        fill_page_1(page)
        if enable_screenshots:
            page.screenshot(path=f"{screenshots_dir}/page1_after.png")

    # Continue with other pages...
    # Note: The page_fillers need to be updated to use Playwright


def auto_fill_inis_form_playwright():
    """
    Main entry point for Playwright-based form filling.
    """
    logger.info("Starting Playwright-based form filling...")

    # Create browser
    browser = HybridBrowser(headless=False)
    browser.start()
    page = browser.page

    try:
        # Initialize form session
        if not initialize_form_session_playwright(page):
            logger.error("Failed to initialize form session")
            return

        # Check for saved application number
        saved_app_number = application_management.get_saved_application_number()

        if saved_app_number:
            logger.info(f"Found saved application number: {saved_app_number}")
            # TODO: Implement retrieve application for Playwright
            # if application_management.retrieve_application(page, saved_app_number):
            #     pass

        # Fill application form
        fill_application_form_playwright(page)

        logger.info("Form filling completed!")

        # Keep browser open for user inspection
        logger.info("Browser will remain open. Press Ctrl+C to exit.")
        while True:
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        browser.close()


if __name__ == "__main__":
    auto_fill_inis_form_playwright()
