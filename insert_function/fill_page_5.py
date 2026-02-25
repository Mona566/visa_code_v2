from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import logging
import re

# 导入工具函数
from .utils import (
    OPERATION_DELAY, POSTBACK_DELAY, POSTBACK_WAIT_DELAY, POSTBACK_BETWEEN_DELAY,
    log_operation, verify_page_state, safe_postback_operation, take_screenshot
)
from .page_detection import (
    check_homepage_redirect, check_and_handle_error_page,
    check_page_redirect_after_field_fill, detect_current_page_state,
    detect_page_number_no_refresh, click_next_button
)
from .form_helpers import (
    fill_dropdown_by_label, select_radio_by_label,
    fill_text_by_label, fill_date_by_label
)
from .application_management import (
    extract_application_number, save_application_number
)

def fill_page_5(browser, wait, screenshots_dir=None):
    """
    Fill the fifth page of the application form
    
    Fields to fill:
    - Are you currently employed in your country of residence: No
    - Are you currently a student in your country of residence: No
    """
    log_operation("fill_page_5", "INFO", "Starting to fill Page 5...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Already on homepage before starting Page 5, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 5 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_5", "INFO", "Page 5 document ready")
        except:
            log_operation("fill_page_5", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_5", "SUCCESS", f"Application Number detected when entering Page 5: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Record initial URL before starting to fill fields
        initial_url = browser.current_url
        log_operation("fill_page_5", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # 1. Are you currently employed in your country of residence
        try:
            log_operation("Currently employed", "INFO", "Selecting currently employed question...")
            select_radio_by_label(browser, wait, "Are you currently employed in your country of residence", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Currently employed", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Currently employed", "WARN", f"Error selecting currently employed: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Currently employed", initial_url)
            if redirect_result:
                return redirect_result
        
        # 2. Are you currently a student in your country of residence
        try:
            log_operation("Currently a student", "INFO", "Selecting currently a student question...")
            select_radio_by_label(browser, wait, "Are you currently a student in your country of residence", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Currently a student", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Currently a student", "WARN", f"Error selecting currently a student: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Currently a student", initial_url)
            if redirect_result:
                return redirect_result
        
        log_operation("fill_page_5", "SUCCESS", "Page 5 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_5", "INFO", f"Current URL after filling Page 5: {current_url}")
        
        # Check for homepage redirect after filling all fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Redirected to homepage after filling all fields, stopping...")
            return "homepage_redirect"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_page_5", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        log_operation("fill_page_5", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_5", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_5", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_5", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_5", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Next/Continue button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_5_filled", output_dir=screenshots_dir)
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_5", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_5", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_5", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_5", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_5", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_5", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_5", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_5", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Next button, check for Application Number
        # Application Number usually appears after submitting page 4 or 5
        time.sleep(2)  # Wait for page to load after navigation
        application_number = extract_application_number(browser, wait)
        if application_number:
            log_operation("fill_page_5", "SUCCESS", f"Application Number detected after Page 5: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        # Return success to indicate successful completion (if no redirect)
        return True
        
    except Exception as e:
        log_operation("fill_page_5", "ERROR", f"Error filling Page 5: {e}")
        import traceback
        traceback.print_exc()
        # Check if we're on homepage (which means we should restart)
        try:
            current_url = browser.current_url
            if "OnlineHome.aspx" in current_url:
                log_operation("fill_page_5", "WARN", "On homepage after error - returning homepage_redirect to trigger restart")
                return "homepage_redirect"
        except:
            pass
        return "error"




