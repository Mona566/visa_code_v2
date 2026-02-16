"""
Page 9 Filler using Playwright

Course Details page - Playwright version
"""

import time
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def fill_page_9(page: Page):
    """
    Fill Page 9 (Course Details).
    """
    logger.info("=" * 50)
    logger.info("Filling Page 9: Course Details")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Check if "Have you paid your course fees" needs to be changed to Yes
        # The radio button ID is: ctl00_ContentPlaceHolder1_rdblstFeesPaid_0 (Yes)
        # and ctl00_ContentPlaceHolder1_rdblstFeesPaid_1 (No)
        try:
            # Check if No is selected
            no_radio = page.locator("#ctl00_ContentPlaceHolder1_rdblstFeesPaid_1")
            if no_radio.is_visible(timeout=3000):
                is_no_checked = no_radio.is_checked()
                if is_no_checked:
                    # Click Yes radio button
                    page.locator("#ctl00_ContentPlaceHolder1_rdblstFeesPaid_0").click(timeout=5000)
                    logger.info("Changed 'Have you paid your course fees' to Yes")
                    return
                else:
                    logger.info("Course fees already set to Yes")
                    return
        except Exception as e:
            logger.warn(f"Could not check/set course fees: {e}")

        # If we get here, form might not be filled - try to fill it
        logger.info("Form may not be filled - attempting to fill fields")

        # Name of School/College
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtNameOfCollege", "Greenfield English College", timeout=5000)
            logger.info("Filled School/College name")
        except Exception as e:
            logger.warn(f"Could not fill School/College: {e}")

        # Course Title
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtCourseTitle", "General English Course", timeout=5000)
            logger.info("Filled Course Title")
        except Exception as e:
            logger.warn(f"Could not fill Course Title: {e}")

        # Duration of Course
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtCourseDuration", "25 weeks", timeout=5000)
            logger.info("Filled Course Duration")
        except Exception as e:
            logger.warn(f"Could not fill Duration: {e}")

        # Course Start Date
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtCourseDurationfrom", "26/01/2026", timeout=5000)
            logger.info("Filled Course Start Date")
        except Exception as e:
            logger.warn(f"Could not fill Start Date: {e}")

        # Course End Date
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtCourseDurationTill", "17/07/2026", timeout=5000)
            logger.info("Filled Course End Date")
        except Exception as e:
            logger.warn(f"Could not fill End Date: {e}")

        # Have you paid your course fees in full - Select YES
        try:
            page.locator("#ctl00_ContentPlaceHolder1_rdblstFeesPaid_0").click(timeout=5000)
            logger.info("Selected: Have you paid your course fees - Yes")
        except Exception as e:
            logger.warn(f"Could not select course fees: {e}")

        # Hours of organized daytime tuition per week
        try:
            page.fill("#ctl00_ContentPlaceHolder1_txtTuitionHours", "18.25 hours", timeout=5000)
            logger.info("Filled Tuition Hours")
        except Exception as e:
            logger.warn(f"Could not fill Tuition Hours: {e}")

        logger.info("Page 9 filled")

    except Exception as e:
        logger.error(f"Failed to fill page 9: {e}")
        # Don't raise - continue with other pages
