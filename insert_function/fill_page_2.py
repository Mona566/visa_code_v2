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
    log_operation, verify_page_state, safe_postback_operation
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

def fill_page_2(browser, wait):
    """
    Fill the second page of the application form
    
    Fields to fill:
    - Surname: "Zhang"
    - Forename: "Wei"
    - Date Of Birth: "18/06/1995"
    - Gender: "Male"
    - Country Of Birth: "People's Republic of China"
    - Current Location: "People's Republic of China"
    - Address Line 1: "No. 88, Zhongshan Road, Pudong New Area, Shanghai"
    - Contact Phone: "+86 138 0000 1234"
    - Contact Email: "zhang_wei@163.com"
    """
    log_operation("fill_page_2", "INFO", "Starting to fill Page 2...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Already on homepage before starting Page 2, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        # Note: After clicking "Save and Continue" from page 1, we should be on a new page
        # The URL might be different, so we'll check for form elements instead
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 2 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_2", "INFO", "Page 2 document ready")
        except:
            log_operation("fill_page_2", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards, but check anyway)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_2", "SUCCESS", f"Application Number detected when entering Page 2: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Record initial URL before starting to fill fields
        initial_url = browser.current_url
        log_operation("fill_page_2", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # 1. Surname
        try:
            # Check for homepage redirect before filling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage before filling Surname, stopping...")
                return "homepage_redirect"
            
            log_operation("Surname", "INFO", "Filling Surname field...")
            fill_text_by_label(browser, wait, "Surname", "Zhang")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Surname", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Surname", "WARN", f"Error filling Surname: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Surname", initial_url)
            if redirect_result:
                return redirect_result
        
        # 2. Forename
        try:
            # Check for homepage redirect before filling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage before filling Forename, stopping...")
                return "homepage_redirect"
            
            log_operation("Forename", "INFO", "Filling Forename field...")
            fill_text_by_label(browser, wait, "Forename", "Wei")
            time.sleep(OPERATION_DELAY)
            
            # Check for homepage redirect after filling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage after filling Forename, stopping...")
                return "homepage_redirect"
        except Exception as e:
            log_operation("Forename", "WARN", f"Error filling Forename: {e}")
        
        # 3. Date Of Birth
        try:
            log_operation("Date Of Birth", "INFO", "Filling Date Of Birth field...")
            # Try to find date input directly first
            date_of_birth_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_txtDateOfBirth"),
                (By.XPATH, "//input[contains(@id, 'DateOfBirth') or contains(@id, 'DOB')]"),
                (By.XPATH, "//input[contains(@name, 'DateOfBirth') or contains(@name, 'DOB')]"),
            ]
            
            date_of_birth_input = None
            for by, selector in date_of_birth_selectors:
                try:
                    date_of_birth_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Date Of Birth", "SUCCESS", f"Found date input: {by}={selector}")
                    break
                except:
                    continue
            
            if date_of_birth_input:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_of_birth_input)
                time.sleep(0.5)
                date_of_birth_input.clear()
                time.sleep(0.2)
                date_of_birth_input.send_keys("18/06/1995")
                log_operation("Date Of Birth", "SUCCESS", "Filled Date Of Birth: 18/06/1995")
            else:
                # Fallback to label-based method
                fill_date_by_label(browser, wait, "Date Of Birth", "", "18/06/1995")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date Of Birth", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Date Of Birth", "WARN", f"Error filling Date Of Birth: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date Of Birth", initial_url)
            if redirect_result:
                return redirect_result
        
        # 4. Gender
        try:
            log_operation("Gender", "INFO", "Selecting Gender...")
            select_radio_by_label(browser, wait, "Gender", "Male", alternative_values=["M", "Male", "1"])
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Gender", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Gender", "WARN", f"Error selecting Gender: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Gender", initial_url)
            if redirect_result:
                return redirect_result
        
        # 5. Country Of Birth
        try:
            # Check for homepage redirect before filling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage before filling Country Of Birth, stopping...")
                return "homepage_redirect"
            
            log_operation("Country Of Birth", "INFO", "Filling Country Of Birth field...")
            fill_dropdown_by_label(browser, wait, "Country Of Birth", "People's Republic of China")
            time.sleep(OPERATION_DELAY)
            
            # Check for homepage redirect after filling (dropdowns can trigger PostBack)
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage after filling Country Of Birth, stopping...")
                return "homepage_redirect"
        except Exception as e:
            log_operation("Country Of Birth", "WARN", f"Error filling Country Of Birth: {e}")
        
        # 6. Current Location
        try:
            # Check for homepage redirect before filling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage before filling Current Location, stopping...")
                return "homepage_redirect"
            
            log_operation("Current Location", "INFO", "Filling Current Location field...")
            fill_dropdown_by_label(browser, wait, "Current Location", "People's Republic of China")
            time.sleep(OPERATION_DELAY)
            
            # Check for homepage redirect after filling (dropdowns can trigger PostBack)
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("fill_page_2", "WARN", "Redirected to homepage after filling Current Location, stopping...")
                return "homepage_redirect"
        except Exception as e:
            log_operation("Current Location", "WARN", f"Error filling Current Location: {e}")
        
        # 7. Address Line 1
        try:
            log_operation("Address Line 1", "INFO", "Filling Address Line 1 field...")
            fill_text_by_label(browser, wait, "Address Line 1", "No. 88, Zhongshan Road, Pudong New Area, Shanghai")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Address Line 1", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Address Line 1", "WARN", f"Error filling Address Line 1: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Address Line 1", initial_url)
            if redirect_result:
                return redirect_result
        
        # 8. Contact Phone
        try:
            log_operation("Contact Phone", "INFO", "Filling Contact Phone field...")
            fill_text_by_label(browser, wait, "Contact Phone", "+86 138 0000 1234")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Contact Phone", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Contact Phone", "WARN", f"Error filling Contact Phone: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Contact Phone", initial_url)
            if redirect_result:
                return redirect_result
        
        # 9. Contact Email
        try:
            log_operation("Contact Email", "INFO", "Filling Contact Email field...")
            fill_text_by_label(browser, wait, "Contact Email", "zhang_wei@163.com")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Contact Email", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Contact Email", "WARN", f"Error filling Contact Email: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Contact Email", initial_url)
            if redirect_result:
                return redirect_result
        
        log_operation("fill_page_2", "SUCCESS", "Page 2 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_2", "INFO", f"Current URL after filling Page 2: {current_url}")
        
        # Check for homepage redirect after filling all fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Redirected to homepage after filling all fields, stopping...")
            return "homepage_redirect"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "application_error":
            log_operation("fill_page_2", "ERROR", "Application error detected - stopping all page filling")
            return "application_error"
        elif error_result == "homepage_redirect":
            log_operation("fill_page_2", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        elif isinstance(error_result, str) and "form_page_" in error_result:
            # Error was resolved and we're on a specific page, return it to continue from there
            log_operation("fill_page_2", "INFO", f"Error resolved, redirected to {error_result}, returning to continue from there")
            return error_result
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        # Note: Page 2 might have a different URL pattern, so we'll verify by checking for form elements
        log_operation("fill_page_2", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_2", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_2", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_2", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_2", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Next/Continue button to go to next page
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_2", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_2", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_2", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_2", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_2", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_2", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_2", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_2", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # Normal completion
        return "success"
        
    except Exception as e:
        log_operation("fill_page_2", "ERROR", f"Error filling Page 2: {e}")
        import traceback
        traceback.print_exc()
        return "error"




