"""
Page 9 Filler using Playwright

Course Details page - simplified version
"""

import time
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


def fill_page_9(page: Page):
    """
    Fill Page 9 (Course Details).
    This page has the "Have you paid your course fees" radio button.
    """
    logger.info("=" * 50)
    logger.info("Filling Page 9: Course Details")
    logger.info("=" * 50)

    try:
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1)

        # Try multiple strategies to find and click the Yes radio for fees

        # Strategy 1: Try by finding label with "Yes" and "fees" or "paid"
        try:
            all_labels = page.locator("label").all()
            for label in all_labels:
                text = label.text_content() or ""
                if "yes" in text.lower() and ("fee" in text.lower() or "paid" in text.lower()):
                    label.click()
                    logger.info("Clicked Yes for fees by label text")
                    return
        except Exception as e:
            logger.debug(f"Strategy 1 failed: {e}")

        # Strategy 2: Try clicking any visible "Yes" option (enumerate and try)
        try:
            yes_options = page.locator("label").filter(has_text="Yes").all()
            # Click each Yes option until one works (typically 2nd or 3rd)
            for yes_opt in yes_options:
                try:
                    yes_opt.click()
                    time.sleep(0.3)
                    logger.debug("Clicked a Yes option")
                except:
                    pass
        except Exception as e:
            logger.debug(f"Strategy 2 failed: {e}")

        # Strategy 3: Try JavaScript to find and click
        try:
            result = page.evaluate("""
                () => {
                    // Find all labels containing Yes and fee/paid
                    const labels = document.querySelectorAll('label');
                    for (const label of labels) {
                        const text = label.textContent.toLowerCase();
                        if (text.includes('yes') && (text.includes('fee') || text.includes('paid'))) {
                            // Find associated input
                            const forAttr = label.getAttribute('for');
                            if (forAttr) {
                                const input = document.getElementById(forAttr);
                                if (input) {
                                    input.click();
                                    return 'clicked';
                                }
                            }
                        }
                    }
                    // Fallback: find any unchecked Yes radio
                    const radios = document.querySelectorAll('input[type="radio"]');
                    for (const r of radios) {
                        if (!r.checked && r.value && (r.value === 'Y' || r.value === 'Yes')) {
                            r.click();
                            return 'clicked_fallback';
                        }
                    }
                    return 'not_found';
                }
            """)
            if result != 'not_found':
                logger.info(f"JavaScript click result: {result}")
                return
        except Exception as e:
            logger.debug(f"Strategy 3 failed: {e}")

        logger.info("Page 9: Attempted to set fees to Yes")

    except Exception as e:
        logger.error(f"Failed to fill page 9: {e}")
