"""
Main Flow for Playwright-based Automation

Orchestrates the form filling process using Playwright.
"""

import os
import time
import logging
from pathlib import Path

from .browser import HybridBrowser
from .playwright_page_detection import (
    detect_current_page_state, check_for_error_page,
    handle_intermediate_page, wait_for_postback_complete
)
from .playwright_page_fillers import dispatch_to_page
from .playwright_helpers import (
    click_button_by_label, log_operation
)

logger = logging.getLogger(__name__)

# Import application management
try:
    from . import application_management
except ImportError:
    application_management = None


# Default visa form URL
DEFAULT_VISA_URL = "https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx"


def initialize_form_session(page):
    """
    Navigate through homepage and privacy to reach form entry.

    Args:
        page: Playwright page object

    Returns:
        bool: True if successfully reached form page
    """
    homepage_url = DEFAULT_VISA_URL

    try:
        # Navigate to homepage
        logger.info(f"Navigating to: {homepage_url}")
        page.goto(homepage_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Check current state
        state = detect_current_page_state(page)
        logger.info(f"Current page state: {state}")

        # Handle any error pages
        if check_for_error_page(page):
            logger.error("Error page detected on initial load")
            return False

        # Step 1: Click "Continue" on homepage
        if state == "homepage":
            logger.info("On homepage - clicking Continue...")

            try:
                # Try multiple methods to find the Continue button
                page.get_by_role("button", name="Continue").click()
            except Exception:
                try:
                    page.get_by_text("Continue").last.click()
                except Exception:
                    page.locator("input[value='Continue']").click()

            logger.info("Waiting for next page...")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

        # Step 2: Handle privacy page (OnlineHome2.aspx)
        state = detect_current_page_state(page)

        if state == "privacy_page":
            logger.info("On privacy page - checking acknowledgment...")

            try:
                # Try to find and check the privacy checkbox
                # Look for common privacy checkbox patterns
                privacy_checkbox = page.locator("input[type='checkbox']").first
                if privacy_checkbox.is_visible():
                    privacy_checkbox.check()
                    logger.info("Privacy checkbox checked")
            except Exception as e:
                logger.warn(f"Could not check privacy checkbox: {e}")

            time.sleep(1)

            # Click Save and Continue / Submit
            logger.info("Clicking submit button...")

            try:
                page.get_by_role("button", name="Save and Continue").click()
            except Exception:
                try:
                    page.get_by_text("Save and Continue").click()
                except Exception:
                    page.locator("input[type='submit']").click()

            # Wait for form page
            logger.info("Waiting for form page...")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)

        # Verify we're on the form page
        state = detect_current_page_state(page)

        if "form_page" in state:
            logger.info(f"Successfully reached form: {state}")
            return True
        else:
            logger.warn(f"Unexpected page state: {state}")
            return False

    except Exception as e:
        logger.error(f"Failed to initialize form session: {e}")
        return False


def retrieve_application(page, application_number: str) -> bool:
    """
    Retrieve an existing application by number.

    Args:
        page: Playwright page object
        application_number: Application number to retrieve

    Returns:
        bool: True if successfully retrieved
    """
    try:
        logger.info(f"Retrieving application: {application_number}")

        # Look for application number input field
        # Common patterns for application retrieval
        try:
            app_input = page.get_by_label("Application Number")
            app_input.fill(application_number)
        except Exception:
            try:
                page.get_by_placeholder("Application Number").fill(application_number)
            except Exception:
                logger.error("Could not find application number input")
                return False

        # Click retrieve button
        try:
            page.get_by_role("button", name="Retrieve").click()
        except Exception:
            page.get_by_text("Retrieve").click()

        # Wait for page to load
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)

        return True

    except Exception as e:
        logger.error(f"Failed to retrieve application: {e}")
        return False


def navigate_to_next_page(page):
    """
    Navigate to the next page in the form.

    Args:
        page: Playwright page object
    """
    logger.info("Navigating to next page...")

    try:
        # Try common "Save and Continue" button patterns
        # Use .first to handle multiple buttons (top/bottom of page)
        try:
            page.get_by_role("button", name="Save and Continue").first.click()
        except Exception:
            try:
                # Try by ID (ASP.NET button)
                page.locator("#ctl00_ButtonBar_btnSaveContinue").click()
            except Exception:
                try:
                    page.locator("input[value='Save and Continue']").first.click()
                except Exception:
                    # Last resort: click any submit button
                    page.locator("input[type='submit']").last.click()

        # Wait for page transition
        wait_for_postback_complete(page)
        time.sleep(2)

    except Exception as e:
        logger.error(f"Failed to navigate to next page: {e}")
        raise


def fill_application_form(page, start_page: int = 1, enable_screenshots: bool = True, screenshots_dir: str = "screenshots_playwright"):
    """
    Fill the complete application form.

    Args:
        page: Playwright page object
        start_page: Page number to start from (default: 1)
        enable_screenshots: Whether to take screenshots (default: True)
        screenshots_dir: Directory for screenshots
    """
    logger.info(f"Starting form filling from page {start_page}")

    # Create screenshots directory if needed
    if enable_screenshots:
        Path(screenshots_dir).mkdir(exist_ok=True)

    # Fill each page
    current_page = start_page

    while current_page <= 10:
        logger.info(f"=" * 50)
        logger.info(f"Filling page {current_page}")
        logger.info(f"=" * 50)

        # Take screenshot before
        if enable_screenshots:
            page.screenshot(path=f"{screenshots_dir}/page{current_page}_before.png")

        # Fill the current page
        dispatch_to_page(page, current_page)

        # Take screenshot after
        if enable_screenshots:
            page.screenshot(path=f"{screenshots_dir}/page{current_page}_after.png")

        # Navigate to next page
        if current_page < 10:
            navigate_to_next_page(page)

        current_page += 1

    logger.info("Form filling completed!")


def auto_fill_inis_form(start_page: int = 1, headless: bool = False, enable_screenshots: bool = True, screenshots_dir: str = "screenshots_playwright"):
    """
    Main entry point for Playwright-based form filling.

    Args:
        start_page: Page number to start from (default: 1)
        headless: Run browser in headless mode
        enable_screenshots: Whether to take screenshots (default: True)
        screenshots_dir: Directory for screenshots

    Returns:
        HybridBrowser: The browser instance (caller should close it)
    """
    logger.info("=" * 60)
    logger.info("Starting Playwright-based INIS form filling")
    logger.info("=" * 60)

    # Create and start browser
    browser = HybridBrowser(headless=headless)
    browser.start()
    page = browser.page

    try:
        # Initialize form session (navigate through homepage/privacy)
        if not initialize_form_session(page):
            logger.error("Failed to initialize form session")
            return browser

        # Check for saved application number
        if application_management:
            saved_app_number = application_management.get_saved_application_number()
            if saved_app_number:
                logger.info(f"Found saved application: {saved_app_number}")

                # Check if we're on homepage - retrieve application
                state = detect_current_page_state(page)
                if state == "homepage":
                    if retrieve_application(page, saved_app_number):
                        logger.info("Application retrieved successfully")

        # Fill the application form
        fill_application_form(page, start_page=start_page, enable_screenshots=enable_screenshots, screenshots_dir=screenshots_dir)

        logger.info("=" * 60)
        logger.info("Form filling completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during form filling: {e}")
    finally:
        # Keep browser open for user inspection
        logger.info("Browser will remain open. Press Ctrl+C to exit.")

    return browser
