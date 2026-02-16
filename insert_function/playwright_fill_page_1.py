"""
Page 1 Filler using Playwright

Visa Type Details page - Playwright version
Optimized for ASP.NET PostBack handling and already-filled forms
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


def fill_page_1(page: Page):
    """
    Fill Visa Type Details page (Page 1).
    Optimized to handle already-filled forms.
    """
    logger.info("=" * 50)
    logger.info("Filling Page 1: Visa Type Details")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Check if form is already filled by checking nationality dropdown
        try:
            nationality_value = page.locator("#ctl00_ContentPlaceHolder1_ddlCountryOfNationality").input_value(timeout=3000)
            if nationality_value and len(nationality_value.strip()) > 0:
                logger.info("Form already filled - skipping fill operations")
                return
        except Exception:
            pass

        logger.info("Form not filled - attempting to fill fields")

        # Fill Country Of Nationality (dropdown)
        try:
            page.select_option("#ctl00_ContentPlaceHolder1_ddlCountryOfNationality",
                            "People's Republic of China", timeout=5000)
            logger.info("Filled Country Of Nationality by ID")
            time.sleep(2)  # Wait for PostBack
        except Exception as e:
            logger.warn(f"Could not fill Country Of Nationality: {e}")

        # Fill Reason for Travel (dropdown)
        try:
            page.select_option("#ctl00_ContentPlaceHolder1_ddlReasonForTravel",
                            "Study", timeout=5000)
            logger.info("Filled Reason for Travel by ID")
            time.sleep(2)
        except Exception as e:
            logger.warn(f"Could not fill Reason for Travel: {e}")

        # Select Visa Type (radio) - Long Stay (D)
        try:
            page.locator("input[type='radio'][value='Long Stay (D)']").first.click(timeout=5000)
            logger.info("Selected Visa Type: Long Stay (D)")
        except Exception as e:
            logger.warn(f"Could not select Visa Type: {e}")

        # Select Journey Type (radio) - Multiple
        try:
            page.locator("input[type='radio'][value='Multiple']").first.click(timeout=5000)
            logger.info("Selected Journey Type: Multiple")
        except Exception as e:
            logger.warn(f"Could not select Journey Type: {e}")

        # Fill Passport Type (dropdown)
        try:
            page.select_option("#ctl00_ContentPlaceHolder1_ddlPassportType",
                            "National Passport", timeout=5000)
            logger.info("Filled Passport Type by ID")
            time.sleep(2)
        except Exception as e:
            logger.warn(f"Could not fill Passport Type: {e}")

        # Fill Passport Number
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtPassportNumber", "112223", timeout=5000)
            logger.info("Filled Passport Number by ID")
        except Exception as e:
            logger.warn(f"Could not fill Passport Number: {e}")

        # Fill Proposed dates
        try:
            date_inputs = page.locator("input[name*='DateOfEntry']").all()
            if date_inputs:
                date_inputs[0].fill("01", timeout=5000)
                if len(date_inputs) > 1:
                    date_inputs[1].fill("03", timeout=5000)
                if len(date_inputs) > 2:
                    date_inputs[2].fill("2026", timeout=5000)
        except Exception as e:
            logger.warn(f"Could not fill From date: {e}")

        try:
            date_inputs = page.locator("input[name*='DateOfExit']").all()
            if date_inputs:
                date_inputs[0].fill("08", timeout=5000)
                if len(date_inputs) > 1:
                    date_inputs[1].fill("03", timeout=5000)
                if len(date_inputs) > 2:
                    date_inputs[2].fill("2026", timeout=5000)
        except Exception as e:
            logger.warn(f"Could not fill To date: {e}")

        logger.info("Page 1 filled")

    except Exception as e:
        log_operation("fill_page_1", "ERROR", f"Failed to fill page 1: {e}")
        # Don't raise - continue with other pages