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

def fill_page_8(browser, wait, screenshots_dir=None):
    """
    Fill the eighth page of the application form
    
    Fields to fill:
    - Personal Status: Single
    - How many dependant children do you have?: 0
    Note: "Please provide the details of any dependant children" is not an input field (may only appear when children > 0)
    """
    log_operation("fill_page_8", "INFO", "Starting to fill Page 8...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Already on homepage before starting Page 8, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 8 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_8", "INFO", "Page 8 document ready")
        except:
            log_operation("fill_page_8", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_8", "SUCCESS", f"Application Number detected when entering Page 8: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Record initial URL before starting to fill fields
        initial_url = browser.current_url
        log_operation("fill_page_8", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # 1. Personal Status - Use retry mechanism to handle stale elements
        try:
            log_operation("Personal Status", "INFO", "Selecting Personal Status...")
            
            personal_status_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_ddlPersonalStatus"),
                (By.XPATH, "//select[contains(@id, 'PersonalStatus') or contains(@id, 'MaritalStatus')]"),
                (By.XPATH, "//select[contains(@name, 'PersonalStatus') or contains(@name, 'MaritalStatus')]"),
                (By.XPATH, "//select[contains(@id, 'ddlPersonal') or contains(@id, 'ddlMarital')]"),
            ]
            
            success = False
            for by, selector in personal_status_selectors:
                try:
                    # Wait for element to be clickable (not just present)
                    select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                    log_operation("Personal Status", "SUCCESS", f"Found Personal Status select by ID/name: {by}={selector}")
                    
                    # Scroll into view
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
                    time.sleep(0.3)
                    
                    # Re-find element to avoid stale reference
                    select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                    
                    # Create Select object and select value
                    select = Select(select_element)
                    
                    # Try different selection methods
                    selection_made = False
                    for method in ['visible_text', 'value', 'index']:
                        try:
                            if method == 'visible_text':
                                select.select_by_visible_text("Single")
                            elif method == 'value':
                                # Try common values for "Single"
                                for val in ['1', 'Single', 'S']:
                                    try:
                                        select.select_by_value(val)
                                        break
                                    except:
                                        continue
                            elif method == 'index':
                                # Find option with "Single" text
                                for idx, option in enumerate(select.options):
                                    if "Single" in option.text or option.text.strip() == "Single":
                                        select.select_by_index(idx)
                                        break
                            
                            time.sleep(0.3)
                            
                            # Verify selection by re-finding element
                            select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                            select = Select(select_element)
                            verify_selection = select.first_selected_option.text
                            
                            if "Single" in verify_selection or verify_selection.strip() == "Single":
                                log_operation("Personal Status", "SUCCESS", f"Selected 'Single' (verified: {verify_selection})")
                                selection_made = True
                                success = True
                                break
                        except Exception as e:
                            if method == 'index':
                                log_operation("Personal Status", "DEBUG", f"Selection method {method} failed: {e}")
                            continue
                    
                    if selection_made:
                        break
                except Exception as e:
                    log_operation("Personal Status", "DEBUG", f"Selector {by}={selector} failed: {e}")
                    continue
            
            if not success:
                # Fallback to label-based method
                log_operation("Personal Status", "INFO", "Trying label-based method...")
                try:
                    fill_dropdown_by_label(browser, wait, "Personal Status", "Single")
                    success = True
                except Exception as e:
                    log_operation("Personal Status", "WARN", f"Label-based method also failed: {e}")
            
                time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Personal Status", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Personal Status", "WARN", f"Error selecting Personal Status: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Personal Status", initial_url)
            if redirect_result:
                return redirect_result
        
        # 2. How many dependant children do you have? - Use retry mechanism to handle stale elements
        try:
            log_operation("Dependant children count", "INFO", "Selecting number of dependant children...")
            
            children_count_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_ddlChildrenCount"),
                (By.ID, "ctl00_ContentPlaceHolder1_ddlDependantChildren"),
                (By.XPATH, "//select[contains(@id, 'Children') or contains(@id, 'Dependant')]"),
                (By.XPATH, "//select[contains(@name, 'Children') or contains(@name, 'Dependant')]"),
                (By.XPATH, "//select[contains(@id, 'ddlChildren') or contains(@id, 'ddlDependant')]"),
            ]
            
            success = False
            for by, selector in children_count_selectors:
                try:
                    # Wait for element to be clickable (not just present)
                    select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                    log_operation("Dependant children count", "SUCCESS", f"Found children count select by ID/name: {by}={selector}")
                    
                    # Scroll into view
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
                    time.sleep(0.3)
                    
                    # Re-find element to avoid stale reference
                    select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                    
                    # Create Select object and select value
                    select = Select(select_element)
                    
                    # Try different selection methods
                    selection_made = False
                    for method in ['visible_text', 'value', 'index']:
                        try:
                            if method == 'visible_text':
                                select.select_by_visible_text("0")
                            elif method == 'value':
                                select.select_by_value("0")
                            elif method == 'index':
                                # Find option with "0" text
                                for idx, option in enumerate(select.options):
                                    option_text = option.text.strip()
                                    if option_text == "0" or option_text.lower() == "zero" or option_text.lower() == "none":
                                        select.select_by_index(idx)
                                        break
                            
                            time.sleep(0.3)
                            
                            # Verify selection by re-finding element
                            select_element = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                            select = Select(select_element)
                            verify_selection = select.first_selected_option.text.strip()
                            
                            if "0" in verify_selection or verify_selection == "0" or verify_selection.lower() == "zero" or verify_selection.lower() == "none":
                                log_operation("Dependant children count", "SUCCESS", f"Selected '0' (verified: {verify_selection})")
                                selection_made = True
                                success = True
                                break
                        except Exception as e:
                            if method == 'index':
                                log_operation("Dependant children count", "DEBUG", f"Selection method {method} failed: {e}")
                            continue
                    
                    if selection_made:
                        break
                except Exception as e:
                    log_operation("Dependant children count", "DEBUG", f"Selector {by}={selector} failed: {e}")
                    continue
            
            if not success:
                # Fallback to label-based method
                log_operation("Dependant children count", "INFO", "Trying label-based method...")
                try:
                    fill_dropdown_by_label(browser, wait, "How many dependant children do you have", "0")
                    success = True
                except Exception as e:
                    log_operation("Dependant children count", "WARN", f"Label-based method also failed: {e}")
            
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Dependant children count", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Dependant children count", "WARN", f"Error selecting number of dependant children: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Dependant children count", initial_url)
            if redirect_result:
                return redirect_result
        
        # Note: "Please provide the details of any dependant children" field is not a text input field
        # It may only appear when number of children > 0, or it may be a read-only/display field
        # Skipping this field as it's not an input field
        
        log_operation("fill_page_8", "SUCCESS", "Page 8 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_8", "INFO", f"Current URL after filling Page 8: {current_url}")
        
        # Check for homepage redirect after filling all fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Redirected to homepage after filling all fields, stopping...")
            return "homepage_redirect"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_page_8", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        log_operation("fill_page_8", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_8", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_8", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_8", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_8", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Next/Continue button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_8_filled", output_dir=screenshots_dir)
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_8", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_8", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_8", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_8", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_8", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_8", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_8", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_8", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Next button, check for Application Number
        # Application Number may appear after submitting page 3 or later
        time.sleep(2)  # Wait for page to load after navigation
        application_number = extract_application_number(browser, wait)
        if application_number:
            log_operation("fill_page_8", "SUCCESS", f"Application Number detected after Page 8: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        # Return success to indicate successful completion (if no redirect)
        return True
        
    except Exception as e:
        log_operation("fill_page_8", "ERROR", f"Error filling Page 8: {e}")
        import traceback
        traceback.print_exc()
        # Check if we're on homepage (which means we should restart)
        try:
            current_url = browser.current_url
            if "OnlineHome.aspx" in current_url:
                log_operation("fill_page_8", "WARN", "On homepage after error - returning homepage_redirect to trigger restart")
                return "homepage_redirect"
        except:
            pass
        return "error"




