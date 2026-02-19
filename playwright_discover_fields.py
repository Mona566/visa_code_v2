"""
Field Discovery Script for INIS Visa Form

This script navigates through all 10 pages of the INIS visa form,
extracts all form fields, takes screenshots, and outputs a structured
JSON of field metadata for updating the page fillers.

Usage:
    conda run -n visa_autofill python playwright_discover_fields.py

With options:
    conda run -n visa_autofill python playwright_discover_fields.py --headless --output fields_discovery.json
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from insert_function.browser import HybridBrowser
from insert_function.playwright_page_detection import detect_current_page_state
from insert_function.playwright_helpers import click_button_by_label

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default visa form URL
DEFAULT_VISA_URL = "https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx"

# Base URL for the INIS website
BASE_URL = "https://www.visas.inis.gov.ie/AVATS"

# Page URLs for the 10 pages
PAGE_URLS = {
    1: "VisaTypeDetails.aspx",
    2: "PersonalDetails.aspx",
    3: "TravelHistory.aspx",
    4: "VisitDetails.aspx",
    5: "AccommodationDetails.aspx",
    6: "VisaDetails.aspx",
    7: "EmploymentDetails.aspx",
    8: "AdditionalDetails.aspx",
    9: "StudentVisa.aspx",
    10: "Summary.aspx"
}


def initialize_form_session(page):
    """
    Navigate through homepage and privacy to reach form entry.
    """
    homepage_url = DEFAULT_VISA_URL

    try:
        logger.info(f"Navigating to: {homepage_url}")
        page.goto(homepage_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Check current state
        state = detect_current_page_state(page)
        logger.info(f"Current page state: {state}")

        # Step 1: Click "Continue" on homepage
        if state == "homepage":
            logger.info("On homepage - clicking Continue...")
            try:
                page.get_by_role("button", name="Continue").click()
            except Exception:
                try:
                    page.get_by_text("Continue").last.click()
                except Exception:
                    page.locator("input[value='Continue']").click()

            logger.info("Waiting for next page...")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

        # Step 2: Handle privacy page
        state = detect_current_page_state(page)

        if state == "privacy_page":
            logger.info("On privacy page - checking acknowledgment...")

            try:
                privacy_checkbox = page.locator("input[type='checkbox']").first
                if privacy_checkbox.is_visible():
                    privacy_checkbox.check()
                    logger.info("Privacy checkbox checked")
            except Exception as e:
                logger.warn(f"Could not check privacy checkbox: {e}")

            time.sleep(1)

            # Click Save and Continue
            logger.info("Clicking submit button...")
            try:
                page.get_by_role("button", name="Save and Continue").click()
            except Exception:
                try:
                    page.get_by_text("Save and Continue").click()
                except Exception:
                    page.locator("input[type='submit']").click()

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


def extract_form_fields(page):
    """
    Extract all form fields from the current page using JavaScript.

    Returns:
        dict: Dictionary containing all form fields with their metadata
    """
    fields_data = {
        "text_inputs": [],
        "select_dropdowns": [],
        "radio_buttons": [],
        "checkboxes": [],
        "textareas": [],
        "hidden_fields": [],
        "buttons": []
    }

    try:
        # JavaScript to extract all form fields
        js_code = """
        function() {
            var fields = {
                text_inputs: [],
                select_dropdowns: [],
                radio_buttons: [],
                checkboxes: [],
                textareas: [],
                hidden_fields: [],
                buttons: []
            };

            // Text inputs
            var textInputs = document.querySelectorAll('input[type="text"]');
            textInputs.forEach(function(el) {
                if (el.id && el.id.indexOf('__') === -1) {  // Skip ASP.NET internal fields
                    fields.text_inputs.push({
                        id: el.id,
                        name: el.name,
                        value: el.value,
                        maxlength: el.maxLength || null,
                        visible: el.offsetParent !== null
                    });
                }
            });

            // Select dropdowns
            var selects = document.querySelectorAll('select');
            selects.forEach(function(el) {
                if (el.id && el.id.indexOf('__') === -1) {
                    var options = [];
                    for (var i = 0; i < el.options.length; i++) {
                        options.push({
                            value: el.options[i].value,
                            text: el.options[i].text
                        });
                    }
                    fields.select_dropdowns.push({
                        id: el.id,
                        name: el.name,
                        options_count: el.options.length,
                        options_sample: options.slice(0, 10),  // First 10 options
                        visible: el.offsetParent !== null
                    });
                }
            });

            // Radio buttons (grouped by name)
            var radioGroups = {};
            var radios = document.querySelectorAll('input[type="radio"]');
            radios.forEach(function(el) {
                if (el.name && el.name.indexOf('ctl00$') !== -1) {
                    if (!radioGroups[el.name]) {
                        radioGroups[el.name] = [];
                    }
                    radioGroups[el.name].push({
                        id: el.id,
                        value: el.value,
                        checked: el.checked,
                        visible: el.offsetParent !== null
                    });
                }
            });
            // Flatten radio groups
            for (var name in radioGroups) {
                fields.radio_buttons.push({
                    name: name,
                    buttons: radioGroups[name]
                });
            }

            // Checkboxes
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(function(el) {
                if (el.id && el.id.indexOf('__') === -1) {
                    fields.checkboxes.push({
                        id: el.id,
                        name: el.name,
                        value: el.value,
                        checked: el.checked,
                        visible: el.offsetParent !== null
                    });
                }
            });

            // Textareas
            var textareas = document.querySelectorAll('textarea');
            textareas.forEach(function(el) {
                if (el.id && el.id.indexOf('__') === -1) {
                    fields.textareas.push({
                        id: el.id,
                        name: el.name,
                        value: el.value,
                        maxlength: el.maxLength || null,
                        visible: el.offsetParent !== null
                    });
                }
            });

            // Hidden fields (important ones only)
            var hiddenInputs = document.querySelectorAll('input[type="hidden"]');
            hiddenInputs.forEach(function(el) {
                if (el.name && el.name.indexOf('ctl00$') !== -1) {
                    fields.hidden_fields.push({
                        id: el.id,
                        name: el.name
                    });
                }
            });

            // Buttons
            var buttons = document.querySelectorAll('input[type="submit"], input[type="button"], button');
            buttons.forEach(function(el) {
                if (el.id && el.id.indexOf('__') === -1) {
                    fields.buttons.push({
                        id: el.id,
                        name: el.name,
                        value: el.value,
                        type: el.type
                    });
                }
            });

            return fields;
        }
        """

        # Execute JavaScript
        result = page.evaluate(js_code)
        return result

    except Exception as e:
        logger.error(f"Error extracting form fields: {e}")
        return fields_data


def extract_field_labels(page):
    """
    Extract labels associated with form fields.

    Returns:
        dict: Mapping of field IDs to their associated labels
    """
    label_map = {}

    try:
        js_code = """
        function() {
            var labelMap = {};

            // Get all labels
            var labels = document.querySelectorAll('label');
            labels.forEach(function(label) {
                var forAttr = label.getAttribute('for');
                if (forAttr) {
                    labelMap[forAttr] = label.textContent.trim();
                }

                // Also check for labels containing inputs
                var input = label.querySelector('input, select, textarea');
                if (input && input.id) {
                    labelMap[input.id] = label.textContent.trim();
                }
            });

            // Also get td-based labels (common in ASP.NET)
            var tds = document.querySelectorAll('td.LabelText');
            tds.forEach(function(td) {
                var nextTd = td.nextElementSibling;
                if (nextTd) {
                    var input = nextTd.querySelector('input, select, textarea');
                    if (input && input.id) {
                        labelMap[input.id] = td.textContent.trim();
                    }
                }
            });

            return labelMap;
        }
        """

        result = page.evaluate(js_code)
        return result

    except Exception as e:
        logger.error(f"Error extracting labels: {e}")
        return label_map


def navigate_to_next_page(page):
    """
    Navigate to the next page in the form.
    """
    logger.info("Navigating to next page...")

    try:
        # Try common "Save and Continue" button patterns
        try:
            page.get_by_role("button", name="Save and Continue").first.click()
        except Exception:
            try:
                page.locator("#ctl00_ButtonBar_btnSaveContinue").click()
            except Exception:
                try:
                    page.locator("input[value='Save and Continue']").first.click()
                except Exception:
                    page.locator("input[type='submit']").last.click()

        # Wait for page transition
        page.wait_for_load_state("domcontentloaded")
        time.sleep(3)

    except Exception as e:
        logger.error(f"Failed to navigate to next page: {e}")
        raise


def discover_fields(headless: bool = False, output_file: str = "fields_discovery.json", screenshots_dir: str = "fields_discovery_screenshots"):
    """
    Main function to discover all form fields across all 10 pages.

    Args:
        headless: Run browser in headless mode
        output_file: Output JSON file path
        screenshots_dir: Directory for screenshots
    """
    logger.info("=" * 60)
    logger.info("Starting Field Discovery")
    logger.info("=" * 60)

    # Create screenshots directory
    Path(screenshots_dir).mkdir(exist_ok=True)

    # Initialize discovery data
    discovery_data = {
        "discovery_date": datetime.now().isoformat(),
        "pages": {}
    }

    # Create and start browser
    browser = HybridBrowser(headless=headless)
    browser.start()
    page = browser.page

    try:
        # Navigate directly to each page URL (no need to fill forms)
        for page_num in range(1, 11):
            logger.info("=" * 50)
            logger.info(f"Discovering fields on Page {page_num}")
            logger.info("=" * 50)

            try:
                # Navigate directly to the page URL
                page_url = f"{BASE_URL}/{PAGE_URLS[page_num]}"
                logger.info(f"Navigating to: {page_url}")
                page.goto(page_url)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                # Get current URL
                current_url = page.url
                logger.info(f"Current URL: {current_url}")

                # Extract form fields
                logger.info("Extracting form fields...")
                fields = extract_form_fields(page)
                logger.info(f"Found {len(fields['text_inputs'])} text inputs, "
                           f"{len(fields['select_dropdowns'])} dropdowns, "
                           f"{len(fields['radio_buttons'])} radio groups, "
                           f"{len(fields['checkboxes'])} checkboxes, "
                           f"{len(fields['textareas'])} textareas")

                # Extract labels
                logger.info("Extracting field labels...")
                labels = extract_field_labels(page)

                # Take screenshot
                screenshot_path = f"{screenshots_dir}/page{page_num}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")

                # Store data
                discovery_data["pages"][f"page_{page_num}"] = {
                    "url": current_url,
                    "fields": fields,
                    "labels": labels,
                    "screenshot": screenshot_path
                }

            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                # Continue to next page
                discovery_data["pages"][f"page_{page_num}"] = {
                    "error": str(e)
                }

        # Save discovery data to JSON
        logger.info(f"Saving discovery data to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert sets to lists for JSON serialization
            json.dump(discovery_data, f, indent=2, default=str)

        logger.info("=" * 60)
        logger.info("Field Discovery Complete!")
        logger.info(f"Results saved to: {output_file}")
        logger.info(f"Screenshots saved to: {screenshots_dir}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during field discovery: {e}")
    finally:
        # Close browser automatically
        try:
            browser.close()
        except Exception:
            pass

    return discovery_data

    return discovery_data


def main():
    parser = argparse.ArgumentParser(
        description="Field Discovery for INIS Visa Form"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="fields_discovery.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--screenshots-dir",
        type=str,
        default="fields_discovery_screenshots",
        help="Directory for screenshots"
    )

    args = parser.parse_args()

    discover_fields(
        headless=args.headless,
        output_file=args.output,
        screenshots_dir=args.screenshots_dir
    )


if __name__ == "__main__":
    main()
