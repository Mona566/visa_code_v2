"""
Form Helper Functions using Playwright

Provides human-like form interaction with fallback strategies for ASP.NET forms.
"""

import logging
import time
from typing import Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator

from .utils import (
    OPERATION_DELAY, POSTBACK_DELAY, POSTBACK_WAIT_DELAY, POSTBACK_BETWEEN_DELAY,
    log_operation
)

logger = logging.getLogger(__name__)


def _find_input_by_label(page: Page, label_text: str) -> Locator:
    """
    Find an input/select element by its label using multiple strategies.

    This handles ASP.NET forms where labels may not have proper 'for' attributes.

    Returns:
        Locator for the input element
    """
    # Strategy 1: Try get_by_label (works if label has for attribute)
    try:
        locator = page.get_by_label(label_text)
        if locator.count() > 0:
            return locator
    except Exception:
        pass

    # Strategy 2: Find label by text, then get associated input
    try:
        # Look for label containing the text
        label_locator = page.locator(f"xpath=//label[contains(text(), '{label_text}')]")
        if label_locator.count() > 0:
            label = label_locator.first
            # Try to find input by 'for' attribute
            label_for = label.get_attribute("for")
            if label_for:
                input_by_id = page.locator(f"#{label_for}")
                if input_by_id.count() > 0:
                    return input_by_id
            # Try to find adjacent input
            input_in_label = label.locator("//following::input[1]")
            if input_in_label.count() > 0:
                return input_in_label
            input_select_in_label = label.locator("//following::select[1]")
            if input_select_in_label.count() > 0:
                return input_select_in_label
    except Exception:
        pass

    # Strategy 3: Look for any element containing the label text, then find input nearby
    try:
        # Look for any element containing the label text (span, div, td, label)
        container = page.locator(f"xpath=//*[contains(text(), '{label_text}')]/following::input[1]")
        if container.count() > 0:
            return container.first
        # Also try select
        container = page.locator(f"xpath=//*[contains(text(), '{label_text}')]/following::select[1]")
        if container.count() > 0:
            return container.first
    except Exception:
        pass

    # Strategy 4: Look for input with matching name or partial ID
    try:
        # Try to find by partial ID match (remove spaces from label)
        partial_id = label_text.replace(" ", "")
        input_by_name = page.locator(f"xpath=//input[contains(@id, '{partial_id}')]")
        if input_by_name.count() > 0:
            return input_by_name.first
    except Exception:
        pass

    # Raise exception if nothing found
    raise Exception(f"Could not find input for label: {label_text}")


def fill_text_by_label(page: Page, label_text: str, value: str, exact: bool = False):
    """
    Fill a text field by its label with fallback strategies.

    Args:
        page: Playwright page object
        label_text: Text of the label (partial match)
        value: Value to fill
        exact: Whether to match label exactly
    """
    try:
        log_operation("fill_text_by_label", "INFO", f"Filling text: {label_text} = {value}")

        # Find the input using multiple strategies
        input_locator = _find_input_by_label(page, label_text)
        input_locator.fill(value)

        time.sleep(OPERATION_DELAY)
        log_operation("fill_text_by_label", "SUCCESS", f"Filled '{label_text}'")
    except Exception as e:
        log_operation("fill_text_by_label", "ERROR", f"Failed to fill '{label_text}': {e}")
        raise


def fill_text_by_id(page: Page, element_id: str, value: str):
    """
    Fill a text field by its CSS ID (fallback method).

    Args:
        page: Playwright page object
        element_id: CSS ID of the element
        value: Value to fill
    """
    try:
        log_operation("fill_text_by_id", "INFO", f"Filling by ID: {element_id} = {value}")
        page.fill(f"#{element_id}", value)
        time.sleep(OPERATION_DELAY)
        log_operation("fill_text_by_id", "SUCCESS", f"Filled element #{element_id}")
    except Exception as e:
        log_operation("fill_text_by_id", "ERROR", f"Failed to fill #{element_id}: {e}")
        raise


def fill_dropdown_by_label(page: Page, label_text: str, value: str):
    """
    Fill a dropdown/select by its label with fallback strategies.

    Args:
        page: Playwright page object
        label_text: Text of the label
        value: Value to select
    """
    try:
        log_operation("fill_dropdown_by_label", "INFO", f"Filling dropdown: {label_text} = {value}")

        # Find the select element
        input_locator = _find_input_by_label(page, label_text)

        # Wait for it to be visible
        input_locator.wait_for(state="visible")

        # Try to select option - Playwright's select_option works with native selects
        # It can accept either the value attribute or the visible text
        input_locator.select_option(value)

        time.sleep(OPERATION_DELAY)
        log_operation("fill_dropdown_by_label", "SUCCESS", f"Selected '{value}' in '{label_text}'")
    except Exception as e:
        log_operation("fill_dropdown_by_label", "ERROR", f"Failed to select in '{label_text}': {e}")
        raise


def select_radio_by_label(page: Page, label_text: str, value: str = None):
    """
    Select a radio button by its label.

    Args:
        page: Playwright page object
        label_text: Text of the label or radio button value
        value: Value to select (optional, will click first matching radio)
    """
    try:
        log_operation("select_radio_by_label", "INFO", f"Selecting radio: {label_text}")

        # Strategy 1: Try to find by label
        try:
            page.get_by_label(label_text).click()
            time.sleep(OPERATION_DELAY)
            log_operation("select_radio_by_label", "SUCCESS", f"Selected radio '{label_text}'")
            return
        except Exception:
            pass

        # Strategy 2: Find by text and click
        try:
            # Look for label containing text, then find radio in same container
            label = page.locator(f"xpath=//label[contains(text(), '{label_text}')]").first
            # Find radio button near this label
            radio = label.locator("//following::input[@type='radio'][1]")
            if radio.count() > 0:
                radio.click()
                time.sleep(OPERATION_DELAY)
                log_operation("select_radio_by_label", "SUCCESS", f"Selected radio '{label_text}'")
                return
        except Exception:
            pass

        # Strategy 3: Look for radio by value
        try:
            page.locator(f"xpath=//input[@type='radio' and @value='{value}']").first.click()
            time.sleep(OPERATION_DELAY)
            log_operation("select_radio_by_label", "SUCCESS", f"Selected radio by value '{value}'")
            return
        except Exception:
            pass

        # Strategy 4: Try get_by_role
        try:
            page.get_by_role("radio", name=label_text).click()
            time.sleep(OPERATION_DELAY)
            log_operation("select_radio_by_label", "SUCCESS", f"Selected radio '{label_text}'")
            return
        except Exception:
            pass

        raise Exception(f"Could not find radio button: {label_text}")

    except Exception as e:
        log_operation("select_radio_by_label", "ERROR", f"Failed to select radio '{label_text}': {e}")
        raise


def check_checkbox_by_label(page: Page, label_text: str, checked: bool = True):
    """
    Check or uncheck a checkbox by its label.

    Args:
        page: Playwright page object
        label_text: Text of the label
        checked: Whether to check (True) or uncheck (False)
    """
    try:
        log_operation("check_checkbox_by_label", "INFO", f"Setting checkbox: {label_text} = {checked}")

        # Try to find checkbox by label
        try:
            locator = page.get_by_label(label_text)
            if checked:
                locator.check()
            else:
                locator.uncheck()
        except Exception:
            # Fallback: find label and checkbox
            label = page.locator(f"xpath=//label[contains(text(), '{label_text}')]").first
            checkbox = label.locator("//preceding::input[@type='checkbox'][1]")
            if checkbox.count() > 0:
                if checked:
                    checkbox.check()
                else:
                    checkbox.uncheck()

        time.sleep(OPERATION_DELAY)
        log_operation("check_checkbox_by_label", "SUCCESS", f"Set checkbox '{label_text}' to {checked}")
    except Exception as e:
        log_operation("check_checkbox_by_label", "ERROR", f"Failed to set checkbox '{label_text}': {e}")
        raise


def click_button_by_label(page: Page, label: str):
    """
    Click a button by its label.

    Args:
        page: Playwright page object
        label: Text on the button
    """
    try:
        log_operation("click_button_by_label", "INFO", f"Clicking button: {label}")

        # Try multiple approaches
        try:
            page.get_by_role("button", name=label).click()
        except Exception:
            try:
                page.get_by_label(label).click()
            except Exception:
                page.get_by_text(label).click()

        time.sleep(OPERATION_DELAY)
        log_operation("click_button_by_label", "SUCCESS", f"Clicked button '{label}'")
    except Exception as e:
        log_operation("click_button_by_label", "ERROR", f"Failed to click button '{label}': {e}")
        raise


def click_button_by_id(page: Page, element_id: str):
    """
    Click a button by its CSS ID (fallback method).

    Args:
        page: Playwright page object
        element_id: CSS ID of the button
    """
    try:
        log_operation("click_button_by_id", "INFO", f"Clicking button by ID: {element_id}")
        page.click(f"#{element_id}")
        time.sleep(OPERATION_DELAY)
        log_operation("click_button_by_id", "SUCCESS", f"Clicked button #{element_id}")
    except Exception as e:
        log_operation("click_button_by_id", "ERROR", f"Failed to click #{element_id}: {e}")
        raise


def wait_for_page_load(page: Page, timeout: int = 30000):
    """
    Wait for page to fully load.

    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    """
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        log_operation("wait_for_page_load", "WARN", f"Page load wait issue: {e}")


def wait_for_postback(page: Page, timeout: int = 30000):
    """
    Wait for ASP.NET PostBack to complete.

    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
        time.sleep(POSTBACK_WAIT_DELAY)
    except Exception as e:
        log_operation("wait_for_postback", "WARN", f"PostBack wait issue: {e}")


def fill_date_by_label(page: Page, label_text: str, day: str, month: str, year: str):
    """
    Fill a date field (typically 3 separate inputs).

    Args:
        page: Playwright page object
        label_text: Label for the date field
        day: Day value
        month: Month value
        year: Year value
    """
    try:
        log_operation("fill_date_by_label", "INFO", f"Filling date: {label_text}")

        # Try to find day/month/year inputs near the label
        try:
            container = page.locator(f"xpath=//*[contains(text(), '{label_text}')]").first.locator("..")
            inputs = container.locator("input").all()

            if len(inputs) >= 3:
                inputs[0].fill(day)
                inputs[1].fill(month)
                inputs[2].fill(year)
            else:
                # Fallback: try by placeholder
                page.get_by_placeholder("DD").fill(day)
                page.get_by_placeholder("MM").fill(month)
                page.get_by_placeholder("YYYY").fill(year)
        except Exception as e:
            log_operation("fill_date_by_label", "ERROR", f"Failed to fill date '{label_text}': {e}")
            raise

        time.sleep(OPERATION_DELAY)
        log_operation("fill_date_by_label", "SUCCESS", f"Filled date for '{label_text}'")
    except Exception as e:
        log_operation("fill_date_by_label", "ERROR", f"Failed to fill date '{label_text}': {e}")
        raise


# Fallback methods for backward compatibility
def fill_dropdown_by_id(page: Page, element_id: str, value: str):
    """Fill a dropdown by CSS ID (fallback method)."""
    try:
        log_operation("fill_dropdown_by_id", "INFO", f"Filling dropdown by ID: {element_id}")
        page.select_option(f"#{element_id}", value)
        time.sleep(OPERATION_DELAY)
        log_operation("fill_dropdown_by_id", "SUCCESS", f"Selected in #{element_id}")
    except Exception as e:
        log_operation("fill_dropdown_by_id", "ERROR", f"Failed to select in #{element_id}: {e}")
        raise


def is_checkbox_checked(page: Page, label_text: str) -> bool:
    """Check if a checkbox is currently checked."""
    try:
        return page.get_by_label(label_text).is_checked()
    except Exception:
        return False
