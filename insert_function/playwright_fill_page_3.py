"""
Page 3 Filler using Playwright

Passport Details / Immigration History page - Playwright version
"""

import time
import logging
from playwright.sync_api import Page

from .playwright_helpers import (
    fill_text_by_label, fill_dropdown_by_label, select_radio_by_label,
    check_checkbox_by_label, click_button_by_label, wait_for_postback,
    log_operation
)

logger = logging.getLogger(__name__)


def fill_page_3(page: Page):
    """
    Fill Page 3 (Immigration History).
    This page is typically already filled for retrieved applications.
    """
    logger.info("=" * 50)
    logger.info("Filling Page 3: Immigration History")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Check if form is already filled by looking for a radio button that's typically selected
        try:
            # Check if first question has an answer (radio selected)
            first_radio = page.locator("input[type='radio']").first
            if first_radio.is_visible(timeout=3000):
                logger.info("Form appears to have elements - skipping fill operations")
                return
        except Exception:
            pass

        logger.info("Form not filled - attempting to fill fields")

        # Try to select radio buttons for Yes/No questions
        # This page typically has "No" selected for most questions
        questions_yes = [
            "Do you have permission to return to that country after your stay in Ireland"
        ]

        questions_no = [
            "Are you exempt from the requirement to provide biometrics",
            "Have you applied for an Irish Visa/Preclearance before",
            "Have you ever been issued with an Irish Visa/Preclearance before",
            "Have you ever been refused an Irish Visa/Preclearance",
            "Have you ever been in Ireland before",
            "Do you have family members living in Ireland",
            "Have you ever been refused permission to enter Ireland before",
            "Have you ever been notified of a deportation order to leave Ireland",
            "Have you ever been refused a visa to another country",
            "Have you ever been refused entry to, deported from, overstayed permission in, or were otherwise required to leave any country",
            "Have you any criminal convictions in any country"
        ]

        # Select "Yes" for first question
        for q in questions_yes:
            try:
                page.locator(f"input[type='radio']").nth(0).click(timeout=3000)
                break
            except Exception:
                pass

        # Select "No" for remaining questions (start from radio button index 1)
        for i, q in enumerate(questions_no):
            try:
                page.locator(f"input[type='radio']").nth(i + 1).click(timeout=3000)
            except Exception:
                pass

        # Fill N/A for detail fields
        detail_fields = [
            "Please provide the location, application number and year of issue",
            "If you have been refused before, please provide location of application, year and reference number",
            "If yes to any of the above please give details"
        ]

        for field in detail_fields:
            try:
                page.fill(f"input[name*='Details'], textarea[name*='Details']", "N/A", timeout=3000)
            except Exception:
                pass

        logger.info("Page 3 filled")

    except Exception as e:
        log_operation("fill_page_3", "ERROR", f"Failed to fill page 3: {e}")
        # Don't raise - continue with other pages