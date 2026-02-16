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

def fill_page_4(browser, wait, screenshots_dir=None):
    """
    Fill the fourth page of the application form
    
    Fields to fill:
    - Passport / Travel Document Number: 112223 (already filled in page 1, but may need to verify/fill again)
    - Type of Travel Document: National Passport (already filled in page 1, but may need to verify/fill again)
    - Issuing Authority / Type: China
    - Date of Issue: 15/03/2021
    - Date of Expiry: 14/03/2031
    - Is this your first Passport?: Yes
    """
    log_operation("fill_page_4", "INFO", "Starting to fill Page 4...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Already on homepage before starting Page 4, stopping...")
            return "homepage_redirect"
        
        # Check for application error before starting
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "application_error":
            log_operation("fill_page_4", "ERROR", "Application error detected before starting Page 4 - stopping all page filling")
            return "application_error"
        elif error_result == "homepage_redirect":
            log_operation("fill_page_4", "WARN", "Error page detected before starting Page 4, redirected to homepage")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 4 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_4", "INFO", "Page 4 document ready")
        except:
            log_operation("fill_page_4", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_4", "SUCCESS", f"Application Number detected when entering Page 4: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Record initial URL before starting to fill fields
        initial_url = browser.current_url
        log_operation("fill_page_4", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # 1. Passport / Travel Document Number (verify or fill if needed)
        try:
            log_operation("Passport Number", "INFO", "Filling/verifying Passport / Travel Document Number field...")
            passport_no_input = None
            passport_no_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_txtPassportNo"),
                (By.XPATH, "//input[contains(@id, 'PassportNo') or contains(@id, 'Passport')]"),
                (By.XPATH, "//input[contains(@name, 'PassportNo') or contains(@name, 'Passport')]"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'Passport')]"),
            ]
            
            for by, selector in passport_no_selectors:
                try:
                    passport_no_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Passport Number", "SUCCESS", f"Found passport number input: {by}={selector}")
                    break
                except:
                    continue
            
            if passport_no_input:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", passport_no_input)
                time.sleep(0.5)
                current_value = passport_no_input.get_attribute("value")
                if current_value != "112223":
                    passport_no_input.clear()
                    time.sleep(0.2)
                    passport_no_input.send_keys("112223")
                    time.sleep(0.3)
                    verify_value = passport_no_input.get_attribute("value")
                    if verify_value == "112223":
                        log_operation("Passport Number", "SUCCESS", f"Filled Passport Number: 112223 (verified: {verify_value})")
                    else:
                        log_operation("Passport Number", "WARN", f"Value not set correctly. Expected '112223', got '{verify_value}'")
                else:
                    log_operation("Passport Number", "INFO", f"Passport Number already set to: {current_value}")
            else:
                # Fallback to label-based method
                fill_text_by_label(browser, wait, "Passport / Travel Document Number", "112223")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Passport Number", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Passport Number", "WARN", f"Error filling Passport Number: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Passport Number", initial_url)
            if redirect_result:
                return redirect_result
        
        # 2. Type of Travel Document (verify or fill if needed)
        try:
            log_operation("Type of Travel Document", "INFO", "Selecting/verifying Type of Travel Document...")
            passport_type_dropdown = None
            passport_type_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_ddlPassportType"),
                (By.XPATH, "//select[contains(@id, 'PassportType') or contains(@id, 'Passport')]"),
                (By.XPATH, "//select[contains(@name, 'PassportType') or contains(@name, 'Passport')]"),
            ]
            
            for by, selector in passport_type_selectors:
                try:
                    passport_type_dropdown = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Type of Travel Document", "SUCCESS", f"Found passport type dropdown: {by}={selector}")
                    break
                except:
                    continue
            
            if passport_type_dropdown:
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", passport_type_dropdown)
                    time.sleep(0.5)
                    select_passport_type = Select(passport_type_dropdown)
                    current_selection = select_passport_type.first_selected_option.text
                    if "National Passport" not in current_selection:
                        select_passport_type.select_by_visible_text("National Passport")
                        time.sleep(0.3)
                        verify_selection = select_passport_type.first_selected_option.text
                        if "National Passport" in verify_selection:
                            log_operation("Type of Travel Document", "SUCCESS", f"Selected 'National Passport' (verified: {verify_selection})")
                        else:
                            log_operation("Type of Travel Document", "WARN", f"Selection not verified. Got: {verify_selection}")
                    else:
                        log_operation("Type of Travel Document", "INFO", f"Type of Travel Document already set to: {current_selection}")
                except Exception as e:
                    log_operation("Type of Travel Document", "WARN", f"Error selecting from dropdown: {e}")
            else:
                # Fallback to label-based method
                fill_dropdown_by_label(browser, wait, "Type of Travel Document", "National Passport")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Type of Travel Document", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Type of Travel Document", "WARN", f"Error selecting Type of Travel Document: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Type of Travel Document", initial_url)
            if redirect_result:
                return redirect_result
        
        # 3. Issuing Authority / Type
        try:
            log_operation("Issuing Authority", "INFO", "Filling Issuing Authority / Type field...")
            # Try to find input directly first by ID
            issuing_authority_input = None
            issuing_authority_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_txtIssuingAuthority"),
                (By.XPATH, "//input[contains(@id, 'IssuingAuthority') or contains(@id, 'Issuing')]"),
                (By.XPATH, "//input[contains(@name, 'IssuingAuthority') or contains(@name, 'Issuing')]"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'Issuing')]"),
            ]
            
            for by, selector in issuing_authority_selectors:
                try:
                    issuing_authority_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Issuing Authority", "SUCCESS", f"Found issuing authority input: {by}={selector}")
                    break
                except:
                    continue
            
            if issuing_authority_input:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", issuing_authority_input)
                time.sleep(0.5)
                issuing_authority_input.clear()
                time.sleep(0.2)
                issuing_authority_input.send_keys("China")
                time.sleep(0.3)
                verify_value = issuing_authority_input.get_attribute("value")
                if "China" in verify_value or verify_value == "China":
                    log_operation("Issuing Authority", "SUCCESS", f"Filled Issuing Authority: China (verified: {verify_value})")
                else:
                    log_operation("Issuing Authority", "WARN", f"Value not set correctly. Expected 'China', got '{verify_value}'")
            else:
                # Fallback to label-based method
                fill_text_by_label(browser, wait, "Issuing Authority / Type", "China")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Issuing Authority", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Issuing Authority", "WARN", f"Error filling Issuing Authority: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Issuing Authority", initial_url)
            if redirect_result:
                return redirect_result
        
        # 4. Date of Issue
        try:
            log_operation("Date of Issue", "INFO", "Filling Date of Issue field...")
            # Try to find date input directly first
            date_of_issue_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_txtDateOfIssue"),
                (By.XPATH, "//input[contains(@id, 'DateOfIssue') or contains(@id, 'IssueDate')]"),
                (By.XPATH, "//input[contains(@name, 'DateOfIssue') or contains(@name, 'IssueDate')]"),
            ]
            
            date_of_issue_input = None
            for by, selector in date_of_issue_selectors:
                try:
                    date_of_issue_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Date of Issue", "SUCCESS", f"Found date of issue input: {by}={selector}")
                    break
                except:
                    continue
            
            if date_of_issue_input:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_of_issue_input)
                time.sleep(0.5)
                date_of_issue_input.clear()
                time.sleep(0.2)
                date_of_issue_input.send_keys("15/03/2021")
                time.sleep(0.3)
                verify_value = date_of_issue_input.get_attribute("value")
                if "15/03/2021" in verify_value or verify_value == "15/03/2021":
                    log_operation("Date of Issue", "SUCCESS", f"Filled Date of Issue: 15/03/2021 (verified: {verify_value})")
                else:
                    log_operation("Date of Issue", "WARN", f"Value not set correctly. Expected '15/03/2021', got '{verify_value}'")
            else:
                # Fallback to label-based method
                fill_date_by_label(browser, wait, "Date of Issue", "", "15/03/2021")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date of Issue", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Date of Issue", "WARN", f"Error filling Date of Issue: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date of Issue", initial_url)
            if redirect_result:
                return redirect_result
        
        # 5. Date of Expiry
        try:
            log_operation("Date of Expiry", "INFO", "Filling Date of Expiry field...")
            # Try to find date input directly first
            date_of_expiry_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_txtDateOfExpiry"),
                (By.XPATH, "//input[contains(@id, 'DateOfExpiry') or contains(@id, 'ExpiryDate')]"),
                (By.XPATH, "//input[contains(@name, 'DateOfExpiry') or contains(@name, 'ExpiryDate')]"),
            ]
            
            date_of_expiry_input = None
            for by, selector in date_of_expiry_selectors:
                try:
                    date_of_expiry_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("Date of Expiry", "SUCCESS", f"Found date of expiry input: {by}={selector}")
                    break
                except:
                    continue
            
            if date_of_expiry_input:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_of_expiry_input)
                time.sleep(0.5)
                date_of_expiry_input.clear()
                time.sleep(0.2)
                date_of_expiry_input.send_keys("14/03/2031")
                time.sleep(0.3)
                verify_value = date_of_expiry_input.get_attribute("value")
                if "14/03/2031" in verify_value or verify_value == "14/03/2031":
                    log_operation("Date of Expiry", "SUCCESS", f"Filled Date of Expiry: 14/03/2031 (verified: {verify_value})")
                else:
                    log_operation("Date of Expiry", "WARN", f"Value not set correctly. Expected '14/03/2031', got '{verify_value}'")
            else:
                # Fallback to label-based method
                fill_date_by_label(browser, wait, "Date of Expiry", "", "14/03/2031")
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date of Expiry", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("Date of Expiry", "WARN", f"Error filling Date of Expiry: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "Date of Expiry", initial_url)
            if redirect_result:
                return redirect_result
        
        # 6. Is this your first Passport?
        try:
            log_operation("First Passport", "INFO", "Selecting first passport question...")
            select_radio_by_label(browser, wait, "Is this your first Passport", "Yes", alternative_values=["Y", "Yes", "1"])
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "First Passport", initial_url)
            if redirect_result:
                return redirect_result
        except Exception as e:
            log_operation("First Passport", "WARN", f"Error selecting first passport: {e}")
            # Check for page redirect even if there was an error
            redirect_result = check_page_redirect_after_field_fill(browser, wait, "First Passport", initial_url)
            if redirect_result:
                return redirect_result
        
        log_operation("fill_page_4", "SUCCESS", "Page 4 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_4", "INFO", f"Current URL after filling Page 4: {current_url}")
        
        # Check for homepage redirect before proceeding
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Redirected to homepage after filling Page 4, stopping...")
            return "homepage_redirect"
        
        # Check for application error
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "application_error":
            log_operation("fill_page_4", "ERROR", "Application error detected - stopping all page filling")
            return "application_error"
        elif error_result == "homepage_redirect":
            log_operation("fill_page_4", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        log_operation("fill_page_4", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_4", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_4", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_4", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_4", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Next/Continue button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_4_filled", output_dir=screenshots_dir)
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_4", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_4", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_4", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_4", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_4", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_4", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_4", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_4", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Next button, check for Application Number
        # Application Number usually appears after submitting page 4 or 5
        time.sleep(2)  # Wait for page to load after navigation
        application_number = extract_application_number(browser, wait)
        if application_number:
            log_operation("fill_page_4", "SUCCESS", f"Application Number detected after Page 4: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        # Normal completion
        return "success"
        
    except Exception as e:
        log_operation("fill_page_4", "ERROR", f"Error filling Page 4: {e}")
        import traceback
        traceback.print_exc()
        return "error"




