"""
Page 2 Filler using Playwright

Personal Details page - Playwright version
Optimized for already-filled forms (retrieved applications)
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


def fill_page_2(page: Page):
    """
    Fill Personal Details page (Page 2).
    Optimized to handle already-filled forms.
    """
    logger.info("=" * 50)
    logger.info("Filling Page 2: Personal Details")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)  # Wait for ASP.NET to fully load

        # Check if form is already filled by looking at surname field
        try:
            surname_locator = page.locator("#ctl00_ContentPlaceHolder1_txtSurname")
            if surname_locator.count() > 0:
                surname_value = surname_locator.first.input_value()
                if surname_value and len(surname_value.strip()) > 0:
                    logger.info(f"Form already filled with surname: {surname_value} - skipping fill operations")
                    return
        except Exception as e:
            logger.info(f"Could not check if form is filled: {e}")

        # If not filled, try to fill fields
        logger.info("Form not filled - attempting to fill fields")

        # Surname
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtSurname", "Zhang", timeout=5000)
            logger.info("Filled Surname by ID")
        except Exception as e:
            logger.warn(f"Could not fill Surname: {e}")

        # Forename
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtForename", "Wei", timeout=5000)
            logger.info("Filled Forename by ID")
        except Exception as e:
            logger.warn(f"Could not fill Forename: {e}")

        # Date of Birth
        try:
            dob_inputs = page.locator("input[name*='DateOfBirth']").all()
            if dob_inputs:
                dob_inputs[0].fill("18", timeout=5000)
                if len(dob_inputs) > 1:
                    dob_inputs[1].fill("06", timeout=5000)
                if len(dob_inputs) > 2:
                    dob_inputs[2].fill("1995", timeout=5000)
                logger.info("Filled Date of Birth")
        except Exception as e:
            logger.warn(f"Could not fill Date of Birth: {e}")

        # Gender
        try:
            page.locator("input[type='radio'][value='M']").first.click(timeout=5000)
            logger.info("Selected Gender: Male")
        except Exception as e:
            logger.warn(f"Could not select Gender: {e}")

        # Country of Birth
        try:
            page.select_option("#ctl00_ContentPlaceHolder1_ddlCountryOfBirth",
                            "People's Republic of China", timeout=5000)
            logger.info("Filled Country of Birth by ID")
            time.sleep(2)
        except Exception as e:
            logger.warn(f"Could not fill Country of Birth: {e}")

        # Current Location
        try:
            page.select_option("#ctl00_ContentPlaceHolder1_ddlCurrentLocation",
                            "People's Republic of China", timeout=5000)
            logger.info("Filled Current Location by ID")
            time.sleep(2)
        except Exception as e:
            logger.warn(f"Could not fill Current Location: {e}")

        # Address Line 1
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtAddressLine1",
                    "No. 88, Zhongshan Road, Pudong New Area, Shanghai", timeout=5000)
            logger.info("Filled Address by ID")
        except Exception as e:
            logger.warn(f"Could not fill Address: {e}")

        # Contact Phone
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtPhone", "+86 138 0000 1234", timeout=5000)
            logger.info("Filled Phone by ID")
        except Exception as e:
            logger.warn(f"Could not fill Phone: {e}")

        # Contact Email
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEmail", "zhang_wei@163.com", timeout=5000)
            logger.info("Filled Email by ID")
        except Exception as e:
            logger.warn(f"Could not fill Email: {e}")

        logger.info("Page 2 filled")

    except Exception as e:
        log_operation("fill_page_2", "ERROR", f"Failed to fill page 2: {e}")
        # Don't raise - continue with other pages