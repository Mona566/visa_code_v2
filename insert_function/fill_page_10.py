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

def fill_page_10(browser, wait, screenshots_dir=None):
    """
    Fill the tenth page of the application form
    
    Fields to fill:
    - Did you receive any assistance in completing this form from an agent/agency?: No
    
    Then click "Sign and Submit" button
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
        
        # ===== MANDATORY FIELDS ON DECLARATION PAGE =====
        # Page 10 is the Declaration page with checkboxes
        # The checkboxes are:
        # - I declare that the information provided is true and correct
        # - I have read and understood the privacy policy
        # - I confirm that the documentation checklist has been completed
        # - I understand that my supporting documents must be forwarded to the relevant office within 5 days

        # Find and check all declaration checkboxes
        try:
            log_operation("Declaration checkboxes", "INFO", "Looking for declaration checkboxes...")

            # Try multiple selectors for declaration checkboxes
            declaration_checkboxes = []
            checkbox_selectors = [
                # Common patterns for declaration checkboxes
                "//input[@type='checkbox' and contains(@id, 'Declaration')]",
                "//input[@type='checkbox' and contains(@id, 'CheckBox')]",
                "//input[@type='checkbox' and contains(@id, 'chk')]",
                "//input[@type='checkbox'][contains(@id, 'ContentPlaceHolder1')]",
            ]

            for selector in checkbox_selectors:
                try:
                    checkboxes = browser.find_elements(By.XPATH, selector)
                    if checkboxes:
                        declaration_checkboxes.extend(checkboxes)
                        log_operation("Declaration checkboxes", "INFO", f"Found {len(checkboxes)} checkboxes using selector: {selector}")
                except Exception as e:
                    log_operation("Declaration checkboxes", "DEBUG", f"Selector {selector} failed: {e}")
                    continue

            # Also try to find checkboxes by label text
            label_keywords = [
                "declare that the information provided is true",
                "read and understood the privacy policy",
                "documentation checklist has been completed",
                "supporting documents must be forwarded"
            ]

            for keyword in label_keywords:
                try:
                    labels = browser.find_elements(By.XPATH, f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                    for label in labels:
                        try:
                            # Try to find checkbox by 'for' attribute
                            label_for = label.get_attribute("for")
                            if label_for:
                                checkbox = browser.find_element(By.ID, label_for)
                                if checkbox not in declaration_checkboxes:
                                    declaration_checkboxes.append(checkbox)
                        except:
                            pass
                        try:
                            # Try to find checkbox in same row
                            checkbox = label.find_element(By.XPATH, ".//preceding::input[@type='checkbox'][1]")
                            if checkbox not in declaration_checkboxes:
                                declaration_checkboxes.append(checkbox)
                        except:
                            pass
                except:
                    continue

            # Check each checkbox
            checked_count = 0
            for checkbox in declaration_checkboxes:
                try:
                    if not checkbox.is_selected():
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        time.sleep(0.3)
                        browser.execute_script("arguments[0].click();", checkbox)
                        time.sleep(0.3)
                        if checkbox.is_selected():
                            checked_count += 1
                            log_operation("Declaration checkboxes", "SUCCESS", f"Checked checkbox")
                    else:
                        checked_count += 1
                        log_operation("Declaration checkboxes", "INFO", "Checkbox already checked")
                except Exception as e:
                    log_operation("Declaration checkboxes", "WARN", f"Error checking checkbox: {e}")

            if checked_count > 0:
                log_operation("Declaration checkboxes", "SUCCESS", f"Checked {checked_count} declaration checkboxes")
            else:
                log_operation("Declaration checkboxes", "WARN", "No checkboxes found to check")

        except Exception as e:
            log_operation("Declaration checkboxes", "WARN", f"Error: {e}")
        
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
        log_operation("fill_page_10", "INFO", "Verifying page state before clicking 'Sign and Submit' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_10", "INFO", "Page state verified, proceeding to click 'Sign and Submit' button...")
            else:
                log_operation("fill_page_10", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_10", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_10", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Sign and Submit button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_10_filled", output_dir=screenshots_dir)
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
        log_operation("fill_page_10", "INFO", "Waiting for page to load after clicking 'Sign and Submit'...")
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




