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

def fill_page_10(browser, wait):
    """
    Fill the tenth page of the application form
    
    Fields to fill:
    - Did you receive any assistance in completing this form from an agent/agency?: No
    
    Then click "Save and Continue" button
    """
    log_operation("fill_page_10", "INFO", "Starting to fill Page 10...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Already on homepage before starting Page 10, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 10 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Redirected to homepage after wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_10", "INFO", "Page 10 document ready")
        except:
            log_operation("fill_page_10", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_10", "SUCCESS", f"Application Number detected when entering Page 10: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Helper function to fill field by direct ID, checking if already filled
        def fill_field_by_id(field_id, value, field_type="text", check_filled=True):
            """Fill a field by direct ID, avoiding duplicate fills"""
            try:
                element = extended_wait.until(EC.presence_of_element_located((By.ID, field_id)))
                
                # Check if already filled (for text/textarea fields)
                if check_filled and field_type in ["text", "textarea"]:
                    current_value = element.get_attribute("value") or ""
                    if current_value and current_value.strip() and current_value.strip() != "dd/mm/yyyy":
                        log_operation(f"fill_page_10", "INFO", f"Field {field_id} already has value '{current_value}', skipping...")
                        return True
                
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)
                
                if field_type == "text" or field_type == "textarea":
                    element.clear()
                    time.sleep(0.2)
                    element.send_keys(value)
                    log_operation(f"fill_page_10", "SUCCESS", f"Filled {field_id} with '{value}'")
                elif field_type == "radio":
                    if not element.is_selected():
                        element.click()
                        log_operation(f"fill_page_10", "SUCCESS", f"Selected radio {field_id}")
                    else:
                        log_operation(f"fill_page_10", "INFO", f"Radio {field_id} already selected, skipping...")
                
                return True
            except Exception as e:
                log_operation(f"fill_page_10", "WARN", f"Error filling {field_id}: {e}")
                return False
        
        # ===== MANDATORY FIELDS =====
        # Did you receive any assistance in completing this form from an agent/agency? * (MANDATORY)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("Assistance from agent/agency", "INFO", "Selecting 'No' for assistance from agent/agency (MANDATORY)...")
            
            # Try multiple strategies to find and select "No" radio button
            # Note: Actual field ID is rdblstAgency, not rdblstAssistance
            assistance_filled = False
            assistance_selectors = [
                ("id", "ctl00_ContentPlaceHolder1_rdblstAgency_1"),  # No option (index 1) - CORRECT ID
                ("id", "ctl00_ContentPlaceHolder1_rdblstAssistance_1"),  # Alternative ID pattern
                ("id", "ctl00_ContentPlaceHolder1_rdblstAgent_1"),  # Alternative ID pattern
                ("xpath", "//input[@type='radio' and contains(@id, 'Agency') and contains(@id, '_1')]"),
                ("xpath", "//input[@type='radio' and contains(@id, 'Assistance') and contains(@id, '_1')]"),
                ("xpath", "//input[@type='radio' and contains(@id, 'Agent') and contains(@id, '_1')]"),
                ("label", "Did you receive any assistance"),
            ]
            
            for strategy, selector in assistance_selectors:
                try:
                    if strategy == "id":
                        # Use direct element manipulation for radio buttons to ensure click works
                        element = extended_wait.until(EC.presence_of_element_located((By.ID, selector)))
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        
                        # Check if already selected
                        if element.is_selected():
                            log_operation("Assistance from agent/agency", "INFO", f"Radio {selector} already selected, skipping...")
                            assistance_filled = True
                            break
                        
                        # Try JavaScript click first (more reliable for radio buttons with PostBack)
                        try:
                            browser.execute_script("arguments[0].click();", element)
                            time.sleep(0.5)
                            # Verify the click worked
                            if element.is_selected():
                                assistance_filled = True
                                log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using ID (JavaScript click): {selector}")
                                break
                            else:
                                # If JavaScript click didn't work, try regular click
                                element.click()
                                time.sleep(0.5)
                                if element.is_selected():
                                    assistance_filled = True
                                    log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using ID (regular click): {selector}")
                                    break
                        except Exception as click_error:
                            log_operation("Assistance from agent/agency", "DEBUG", f"JavaScript click failed: {click_error}, trying regular click...")
                            element.click()
                            time.sleep(0.5)
                            if element.is_selected():
                                assistance_filled = True
                                log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using ID (fallback click): {selector}")
                                break
                        
                        # If we reach here, click didn't work
                        log_operation("Assistance from agent/agency", "DEBUG", f"Click on {selector} did not select the radio button, trying next strategy...")
                        continue
                    elif strategy == "xpath":
                        element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        
                        # Check if already selected
                        if element.is_selected():
                            log_operation("Assistance from agent/agency", "INFO", f"Radio (XPath) already selected, skipping...")
                            assistance_filled = True
                            break
                        
                        # Try JavaScript click first
                        try:
                            browser.execute_script("arguments[0].click();", element)
                            time.sleep(0.5)
                            if element.is_selected():
                                assistance_filled = True
                                log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using XPath (JavaScript click): {selector}")
                                break
                            else:
                                element.click()
                                time.sleep(0.5)
                                if element.is_selected():
                                    assistance_filled = True
                                    log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using XPath (regular click): {selector}")
                                    break
                        except Exception as click_error:
                            log_operation("Assistance from agent/agency", "DEBUG", f"XPath click failed: {click_error}")
                            continue
                    else:  # label
                        # Try to find label and then find associated radio button
                        labels = browser.find_elements(By.XPATH, f"//label[contains(text(), '{selector}')]")
                        if labels:
                            for label in labels:
                                # Try to find associated input by 'for' attribute
                                label_for = label.get_attribute("for")
                                if label_for:
                                    try:
                                        radio = browser.find_element(By.ID, label_for)
                                        if radio.get_attribute("type") == "radio" and radio.get_attribute("value") == "No":
                                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                            time.sleep(0.3)
                                            if not radio.is_selected():
                                                radio.click()
                                                assistance_filled = True
                                                log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using label: {selector}")
                                                break
                                    except:
                                        continue
                                # If no 'for' attribute, try to find radio in same row
                                try:
                                    row = label.find_element(By.XPATH, "./ancestor::tr")
                                    radios = row.find_elements(By.XPATH, ".//input[@type='radio']")
                                    for radio in radios:
                                        radio_id = radio.get_attribute("id")
                                        radio_value = radio.get_attribute("value")
                                        # Check if this is the "No" option (index 1 or value 0)
                                        # From debug: rdblstAgency_0 (Yes, value=1), rdblstAgency_1 (No, value=0)
                                        if radio_id and "_1" in radio_id and ("Agency" in radio_id or "Assistance" in radio_id or "Agent" in radio_id):
                                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                            time.sleep(0.5)
                                            if not radio.is_selected():
                                                # Try JavaScript click first
                                                try:
                                                    browser.execute_script("arguments[0].click();", radio)
                                                    time.sleep(0.5)
                                                    if radio.is_selected():
                                                        assistance_filled = True
                                                        log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using label (JavaScript click): {selector}, radio ID: {radio_id}")
                                                        break
                                                    else:
                                                        radio.click()
                                                        time.sleep(0.5)
                                                        if radio.is_selected():
                                                            assistance_filled = True
                                                            log_operation("Assistance from agent/agency", "SUCCESS", f"Filled using label (regular click): {selector}, radio ID: {radio_id}")
                                                            break
                                                except Exception as click_error:
                                                    log_operation("Assistance from agent/agency", "DEBUG", f"Label click failed: {click_error}")
                                                    continue
                                            else:
                                                assistance_filled = True
                                                log_operation("Assistance from agent/agency", "INFO", f"Radio already selected via label: {radio_id}")
                                                break
                                    if assistance_filled:
                                        break
                                except:
                                    continue
                        if assistance_filled:
                            break
                except Exception as e:
                    log_operation("Assistance from agent/agency", "DEBUG", f"Strategy {strategy} failed: {e}")
                    continue
            
            if not assistance_filled:
                log_operation("Assistance from agent/agency", "WARN", "Could not fill assistance field using any strategy")
            
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("Assistance from agent/agency", "WARN", f"Error: {e}")
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_page_10", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        log_operation("fill_page_10", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_10", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_10", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_10", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Save and Continue button to go to next page
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_10", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_10", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_10", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_10", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_10", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_10", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_10", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_10", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Save and Continue button, wait for page to load
        log_operation("fill_page_10", "INFO", "Waiting for page to load after clicking 'Save and Continue'...")
        time.sleep(3)  # Wait for page to load after navigation
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(2)
        
        # Check if we're on the thank you/submission confirmation page
        current_url = browser.current_url
        page_source = browser.page_source.lower()
        page_text = ""
        try:
            page_text = browser.find_element(By.TAG_NAME, "body").text.lower()
        except:
            pass
        
        # Check for thank you/submission confirmation page
        # Also check for CompleteFormSummary.aspx which is the submission confirmation page
        is_thank_you_page = False
        thank_you_keywords = [
            "thank you",
            "your online application has been submitted",
            "application has been submitted",
            "submitted to the relevant irish embassy",
            "submitted to the relevant irish consulate",
            "submitted to the relevant visa office",
            "completeformsummary",
            "form summary",
            "application summary"
        ]
        
        # Check URL first
        if "CompleteFormSummary.aspx" in current_url:
            log_operation("fill_page_10", "SUCCESS", f"Detected submission confirmation page by URL: {current_url}")
            is_thank_you_page = True
        else:
            # Check page content
            for keyword in thank_you_keywords:
                if keyword in page_source or keyword in page_text:
                    is_thank_you_page = True
                    log_operation("fill_page_10", "SUCCESS", f"Detected thank you/submission confirmation page (keyword: '{keyword}')")
                    break
        
        if is_thank_you_page:
            log_operation("fill_page_10", "INFO", "Application submission completed successfully. Page will remain on thank you page.")
            
            # Check for Application Number on thank you page
            application_number = extract_application_number(browser, wait)
            if application_number:
                log_operation("fill_page_10", "SUCCESS", f"Application Number detected on thank you page: {application_number}")
                save_application_number(application_number)
            
            # Print success message and wait for user to press Enter
            print("\n" + "="*60)
            print("[SUCCESS] Application has been submitted successfully!")
            print("[INFO] Page will remain on thank you page.")
            print("[INFO] Press Enter to exit and close browser...")
            print("="*60 + "\n")
            
            # Wait for user to press Enter (infinite wait)
            input()
            
            # Return special status to indicate completion
            return "submission_complete"
        else:
            # Not on thank you page, check for Application Number normally
            application_number = extract_application_number(browser, wait)
            if application_number:
                log_operation("fill_page_10", "SUCCESS", f"Application Number detected after Page 10: {application_number}")
                # Save Application Number to a file for future use (with validation)
                save_application_number(application_number)
            
            # Return success to indicate successful completion (if no redirect)
            return True
        
    except Exception as e:
        log_operation("fill_page_10", "ERROR", f"Error filling Page 10: {e}")
        import traceback
        traceback.print_exc()
        # Check if we're on homepage (which means we should restart)
        try:
            current_url = browser.current_url
            if "OnlineHome.aspx" in current_url:
                log_operation("fill_page_10", "WARN", "On homepage after error - returning homepage_redirect to trigger restart")
                return "homepage_redirect"
        except:
            pass
        return "error"




