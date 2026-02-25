"""
Page 9 Filler using Playwright

Student Visa page (Page 9) - Playwright version
Based on actual field structure from debug_page9_source.html
"""

import time
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def fill_page_9(page: Page):
    """
    Fill Page 9 (Student Visa Details).

    Based on actual fields from debug_page9_source.html:
    - Radio: rdblstAcceptedByCollege, rdblstStudiedBefore, rdblstSpeakEnglish, rdblstSponsor
    - Text: txtSchoolColl1-5 (textareas), txtQualObtained1-5
    - Text: txtEduFrom1-5, txtEduTill1-5 (dates)
    - Text: txtEmployerName1-5 (textareas), txtPositionHeld1-5
    - Text: txtEmpFrom1-5, txtEmpTill1-5 (dates)
    - Textarea: txtEduGaps, txtOtherFundDtl
    """
    logger.info("=" * 50)
    logger.info("Filling Page 9: Student Visa Details")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Check if form is already filled - check first education field
        try:
            school_value = page.locator("#ctl00_ContentPlaceHolder1_txtSchoolColl1").input_value(timeout=3000)
            if school_value and len(school_value.strip()) > 0:
                logger.info("Form already filled - skipping fill operations")
                return
        except Exception:
            pass

        logger.info("Form not filled - attempting to fill fields")

        # === Section: Have you been accepted on a course of study in Ireland? ===
        try:
            # Select Yes
            page.locator("#ctl00_ContentPlaceHolder1_rdblstAcceptedByCollege_0").click(timeout=5000)
            logger.info("Selected: Accepted by college - Yes")
            time.sleep(1)
        except Exception as e:
            logger.warn(f"Could not select Accepted by college: {e}")

        # === Section: Have you studied in Ireland before? ===
        try:
            # Select No
            page.locator("#ctl00_ContentPlaceHolder1_rdblstStudiedBefore_1").click(timeout=5000)
            logger.info("Selected: Studied before - No")
            time.sleep(1)
        except Exception as e:
            logger.warn(f"Could not select Studied before: {e}")

        # === Section: Do you speak English? ===
        try:
            # Select Yes
            page.locator("#ctl00_ContentPlaceHolder1_rdblstSpeakEnglish_0").click(timeout=5000)
            logger.info("Selected: Speak English - Yes")
            time.sleep(1)
        except Exception as e:
            logger.warn(f"Could not select Speak English: {e}")

        # === Education History - School/College 1 ===
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtSchoolColl1", "Test School", timeout=5000)
            logger.info("Filled School/College 1")
        except Exception as e:
            logger.warn(f"Could not fill School/College 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtQualObtained1", "High School Diploma", timeout=5000)
            logger.info("Filled Qualification 1")
        except Exception as e:
            logger.warn(f"Could not fill Qualification 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEduFrom1", "01/09/2020", timeout=5000)
            logger.info("Filled Education From 1")
        except Exception as e:
            logger.warn(f"Could not fill Education From 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEduTill1", "01/06/2024", timeout=5000)
            logger.info("Filled Education Till 1")
        except Exception as e:
            logger.warn(f"Could not fill Education Till 1: {e}")

        # === Employment History - Employer 1 ===
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEmployerName1", "Previous Employer", timeout=5000)
            logger.info("Filled Employer Name 1")
        except Exception as e:
            logger.warn(f"Could not fill Employer Name 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtPositionHeld1", "Software Developer", timeout=5000)
            logger.info("Filled Position Held 1")
        except Exception as e:
            logger.warn(f"Could not fill Position Held 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEmpFrom1", "01/01/2023", timeout=5000)
            logger.info("Filled Employment From 1")
        except Exception as e:
            logger.warn(f"Could not fill Employment From 1: {e}")

        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEmpTill1", "01/08/2024", timeout=5000)
            logger.info("Filled Employment Till 1")
        except Exception as e:
            logger.warn(f"Could not fill Employment Till 1: {e}")

        # === Sponsor Section ===
        try:
            # Select "Own Funds" or similar
            page.locator("#ctl00_ContentPlaceHolder1_rdblstSponsor_0").click(timeout=5000)
            logger.info("Selected Sponsor")
            time.sleep(1)
        except Exception as e:
            logger.warn(f"Could not select Sponsor: {e}")

        # === Other Funds Details (if applicable) ===
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtOtherFundDtl", "Personal savings", timeout=5000)
            logger.info("Filled Other Fund Details")
        except Exception as e:
            logger.warn(f"Could not fill Other Fund Details: {e}")

        # === Education Gaps ===
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtEduGaps", "No gaps in education", timeout=5000)
            logger.info("Filled Education Gaps")
        except Exception as e:
            logger.warn(f"Could not fill Education Gaps: {e}")

        logger.info("Page 9 filled")

    except Exception as e:
        logger.error(f"Failed to fill page 9: {e}")
        # Don't raise - continue with other pages
