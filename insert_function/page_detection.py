from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import logging
import re
import os

# 导入工具函数
from .utils import (
    OPERATION_DELAY, POSTBACK_DELAY, POSTBACK_WAIT_DELAY, POSTBACK_BETWEEN_DELAY,
    log_operation, verify_page_state
)
# 注意：不在这里导入 application_management 中的函数，避免循环导入
# 在 restart_from_homepage 函数中使用延迟导入

def check_and_handle_error_page(browser, wait):
    """
    Check if the page shows an application error message.
    If error is detected, refresh the page and check current page configuration.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        str or bool: 
            - "application_error" if error was detected (critical error, should stop all page filling)
            - "homepage_redirect" if error was detected and page redirected to homepage after refresh
            - True if error was detected and handled (but not redirected to homepage)
            - False if no error was detected
    """
    try:
        # First check URL for error pages
        current_url = browser.current_url
        if "ApplicationError.aspx" in current_url or "Error.aspx" in current_url:
            log_operation("check_and_handle_error_page", "ERROR", f"Detected error page URL: {current_url}")
            # Keep refreshing until error is resolved
            # After 5 failed attempts, navigate to homepage and restart
            max_initial_refresh_attempts = 5  # Try 5 times first
            max_refresh_attempts = 50  # Maximum total attempts to prevent infinite loop
            refresh_count = 0
            max_total_wait_time = 300  # Maximum total wait time: 5 minutes
            start_time = time.time()
            
            while refresh_count < max_refresh_attempts:
                # Check if we've exceeded maximum wait time
                elapsed_time = time.time() - start_time
                if elapsed_time > max_total_wait_time:
                    log_operation("check_and_handle_error_page", "ERROR", f"Exceeded maximum wait time ({max_total_wait_time}s) - navigating to homepage to restart")
                    # Navigate to homepage and restart
                    try:
                        browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                        time.sleep(3)
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        log_operation("check_and_handle_error_page", "INFO", "Navigated to homepage after timeout, returning homepage_redirect to restart")
                        return "homepage_redirect"
                    except Exception as e:
                        log_operation("check_and_handle_error_page", "ERROR", f"Failed to navigate to homepage: {e}")
                        return "application_error"
                
                refresh_count += 1
                log_operation("check_and_handle_error_page", "INFO", f"Refreshing page to recover from error (attempt {refresh_count})...")
                browser.refresh()
                time.sleep(3)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(2)
                
                new_url_after = browser.current_url
                log_operation("check_and_handle_error_page", "INFO", f"URL after refresh {refresh_count}: {new_url_after}")
                
                # Check if still on error page
                if "ApplicationError.aspx" in new_url_after or "Error.aspx" in new_url_after:
                    # If we've tried 5 times and still on error page, navigate to homepage and restart
                    if refresh_count >= max_initial_refresh_attempts:
                        log_operation("check_and_handle_error_page", "WARN", f"Still on error page after {refresh_count} refresh attempts - navigating to homepage to restart from beginning")
                        try:
                            browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                            time.sleep(3)
                            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                            log_operation("check_and_handle_error_page", "INFO", "Navigated to homepage after 5 failed refresh attempts, returning homepage_redirect to restart")
                            return "homepage_redirect"
                        except Exception as e:
                            log_operation("check_and_handle_error_page", "ERROR", f"Failed to navigate to homepage: {e}")
                            # Continue trying to refresh if navigation failed
                            continue
                    else:
                        log_operation("check_and_handle_error_page", "WARN", f"Still on error page after refresh {refresh_count}, will continue refreshing...")
                        continue
                
                # Error page is gone, now detect current page
                log_operation("check_and_handle_error_page", "SUCCESS", f"Error page resolved after {refresh_count} refresh(es), detecting current page...")
                
                # Check if redirected to homepage
                if "OnlineHome.aspx" in new_url_after:
                    log_operation("check_and_handle_error_page", "WARN", "Error page redirected to homepage after refresh - returning homepage_redirect")
                    return "homepage_redirect"
                
                # Detect current page number if on form page
                if "VisaTypeDetails.aspx" in new_url_after:
                    page_number = None
                    try:
                        # Check for Page 1 fields
                        country_dropdown = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                        if country_dropdown:
                            page_number = 1
                            log_operation("check_and_handle_error_page", "INFO", "Detected: Page 1")
                    except:
                        pass
                    
                    if page_number is None:
                        try:
                            # Check for Page 2 fields
                            surname_input = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtSurname")
                            if surname_input:
                                page_number = 2
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 2")
                        except:
                            pass
                    
                    if page_number is None:
                        try:
                            # Check for Page 3/4/5/6/7/8/9 fields
                            page_source_check = browser.page_source
                            if "No Of Years" in page_source_check or "permission to return" in page_source_check:
                                page_number = 3
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 3")
                            elif "Date of Issue" in page_source_check or "Is this your first Passport" in page_source_check:
                                page_number = 4
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 4")
                            elif "Are you currently employed" in page_source_check or "Are you currently a student" in page_source_check:
                                page_number = 5
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 5")
                            elif "Will you be travelling with any other person" in page_source_check:
                                page_number = 6
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 6")
                            elif "Is the contact/host in Ireland personally known" in page_source_check:
                                page_number = 7
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 7")
                            elif "Personal Status" in page_source_check or "How many dependant children" in page_source_check:
                                page_number = 8
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 8")
                            elif "Have you been accepted on a course of study" in page_source_check or "Course of Study in Ireland" in page_source_check:
                                page_number = 9
                                log_operation("check_and_handle_error_page", "INFO", "Detected: Page 9")
                        except:
                            pass
                    
                    if page_number:
                        log_operation("check_and_handle_error_page", "INFO", f"Error resolved, on form page {page_number} - returning form_page_{page_number}")
                        return f"form_page_{page_number}"
                    else:
                        log_operation("check_and_handle_error_page", "WARN", "Error resolved, on form page but could not detect page number - returning False to continue")
                        return False
                
                # If on intermediate page, handle it
                if "OnlineHome2.aspx" in new_url_after:
                    log_operation("check_and_handle_error_page", "INFO", "After error refresh, on intermediate page - attempting to handle")
                    if handle_intermediate_page(browser, wait):
                        final_url = browser.current_url
                        if "VisaTypeDetails.aspx" in final_url:
                            # Detect page number after handling intermediate page
                            page_number = None
                            try:
                                country_dropdown = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                                if country_dropdown:
                                    page_number = 1
                            except:
                                pass
                            if page_number is None:
                                try:
                                    surname_input = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtSurname")
                                    if surname_input:
                                        page_number = 2
                                except:
                                    pass
                            if page_number:
                                return f"form_page_{page_number}"
                            return False
                        elif "OnlineHome.aspx" in final_url:
                            return "homepage_redirect"
                    
                # If we get here, error is resolved but page type is unknown
                log_operation("check_and_handle_error_page", "INFO", "Error resolved, but page type is unknown - returning False to continue")
                return False
            
            # If we exhausted all refresh attempts (should not reach here due to continue statement above)
            log_operation("check_and_handle_error_page", "ERROR", f"Error page persists after {max_refresh_attempts} refresh attempts - returning application_error")
            return "application_error"
        
        # Error message keywords to search for
        error_keywords = [
            "An error has occured in the application",
            "An error has occurred in the application",
            "the system administrator has been informed",
            "Please try again",
            "error has occured",
            "error has occurred"
        ]
        
        # Get page source and text
        page_source = browser.page_source.lower()
        try:
            page_text = browser.find_element(By.TAG_NAME, "body").text.lower()
        except:
            page_text = ""
        
        # Check if any error keywords are present in page source or body text
        error_detected = False
        detected_keyword = None
        for keyword in error_keywords:
            if keyword.lower() in page_source or keyword.lower() in page_text:
                error_detected = True
                detected_keyword = keyword
                print(f"[ERROR] Detected application error message: '{keyword}'")
                log_operation("check_and_handle_error_page", "ERROR", f"Detected error keyword in page: '{keyword}'")
                break
        
        # Also check for error elements in the DOM with multiple strategies
        if not error_detected:
            try:
                # Strategy 1: Check for MainHeadersText class (common error container)
                main_header_elements = browser.find_elements(By.CSS_SELECTOR, ".MainHeadersText, td.MainHeadersText")
                for elem in main_header_elements:
                    try:
                        if elem.is_displayed():
                            elem_text = elem.text.lower()
                            for keyword in error_keywords:
                                if keyword.lower() in elem_text:
                                    error_detected = True
                                    detected_keyword = keyword
                                    error_text = elem.text.strip()
                                    print(f"[ERROR] Found error in MainHeadersText element: {error_text[:200]}")
                                    log_operation("check_and_handle_error_page", "ERROR", f"Found error in MainHeadersText: '{keyword}'")
                                    break
                            if error_detected:
                                break
                    except:
                        continue
            except Exception as e:
                print(f"[DEBUG] Error checking MainHeadersText: {e}")
        
        # Strategy 2: Check for error elements by XPath with more comprehensive patterns
        if not error_detected:
            try:
                # Check for elements containing error text (even if split by HTML tags)
                xpath_patterns = [
                    "//*[contains(text(), 'error has occured')]",
                    "//*[contains(text(), 'error has occurred')]",
                    "//*[contains(text(), 'system administrator has been informed')]",
                    "//*[contains(text(), 'Please try again')]",
                    "//td[contains(@class, 'MainHeadersText')]",
                    "//*[contains(@class, 'MainHeadersText')]",
                    "//tr[.//*[contains(text(), 'error has occured')]]",
                    "//tr[.//*[contains(text(), 'error has occurred')]]"
                ]
                
                for xpath_pattern in xpath_patterns:
                    try:
                        error_elements = browser.find_elements(By.XPATH, xpath_pattern)
                        if error_elements:
                            for err_elem in error_elements:
                                try:
                                    if err_elem.is_displayed():
                                        # Get text from element and its children
                                        elem_text = err_elem.text.lower()
                                        inner_html = err_elem.get_attribute("innerHTML") or ""
                                        
                                        # Check if any error keyword is in the text or innerHTML
                                        for keyword in error_keywords:
                                            if keyword.lower() in elem_text or keyword.lower() in inner_html.lower():
                                                error_detected = True
                                                detected_keyword = keyword
                                                error_text = err_elem.text.strip()
                                                print(f"[ERROR] Found error element (XPath: {xpath_pattern}): {error_text[:200]}")
                                                log_operation("check_and_handle_error_page", "ERROR", f"Found error element: '{keyword}'")
                                                break
                                        if error_detected:
                                            break
                                except:
                                    continue
                            if error_detected:
                                break
                    except:
                        continue
            except Exception as e:
                print(f"[DEBUG] Error checking XPath patterns: {e}")
        
        # Strategy 3: Check page source for error patterns even if not in visible text
        if not error_detected:
            try:
                # Check for error message patterns in page source (handles cases where text is split by HTML)
                error_patterns = [
                    "error has occured",
                    "error has occurred",
                    "system administrator has been informed",
                    "please try again"
                ]
                for pattern in error_patterns:
                    if pattern in page_source:
                        # Verify it's actually in a visible element by checking if it's near MainHeadersText or in a td
                        if "mainheaderstext" in page_source or "td" in page_source:
                            error_detected = True
                            detected_keyword = pattern
                            print(f"[ERROR] Detected error pattern in page source: '{pattern}'")
                            log_operation("check_and_handle_error_page", "ERROR", f"Detected error pattern in page source: '{pattern}'")
                            break
            except Exception as e:
                print(f"[DEBUG] Error checking page source patterns: {e}")
        
        if error_detected:
            log_operation("check_and_handle_error_page", "ERROR", f"Application error detected: '{detected_keyword}' - Attempting to refresh and recover...")
            print(f"\n{'='*60}")
            print(f"[ERROR] Application error detected: '{detected_keyword}'")
            print(f"[INFO] Attempting to refresh page and recover...")
            print(f"{'='*60}\n")
            
            # Get current URL before refresh
            url_before_refresh = browser.current_url
            log_operation("check_and_handle_error_page", "INFO", f"URL before refresh: {url_before_refresh}")
            
            # Refresh the page to try to recover
            try:
                browser.refresh()
                log_operation("check_and_handle_error_page", "INFO", "Page refreshed, waiting for page to load...")
                time.sleep(3)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(2)
            except Exception as e:
                log_operation("check_and_handle_error_page", "WARN", f"Error during page refresh: {e}")
            
            # Check if error still exists after refresh
            page_source_after = browser.page_source.lower()
            page_text_after = ""
            try:
                page_text_after = browser.find_element(By.TAG_NAME, "body").text.lower()
            except:
                pass
            
            error_still_exists = False
            for keyword in error_keywords:
                if keyword.lower() in page_source_after or keyword.lower() in page_text_after:
                    error_still_exists = True
                    log_operation("check_and_handle_error_page", "ERROR", f"Error still exists after refresh: '{keyword}'")
                    break
            
            # Also check for error elements in DOM after refresh
            if not error_still_exists:
                try:
                    main_header_elements = browser.find_elements(By.CSS_SELECTOR, ".MainHeadersText, td.MainHeadersText")
                    for elem in main_header_elements:
                        try:
                            if elem.is_displayed():
                                elem_text = elem.text.lower()
                                for keyword in error_keywords:
                                    if keyword.lower() in elem_text:
                                        error_still_exists = True
                                        log_operation("check_and_handle_error_page", "ERROR", f"Error still exists in MainHeadersText after refresh: '{keyword}'")
                                        break
                                if error_still_exists:
                                    break
                        except:
                            continue
                except:
                    pass
            
            # If error still exists, return application_error
            if error_still_exists:
                log_operation("check_and_handle_error_page", "ERROR", "Error persists after refresh - returning application_error")
                return "application_error"
            
            # Error is gone after refresh, now detect current page state
            log_operation("check_and_handle_error_page", "INFO", "Error resolved after refresh, detecting current page state...")
            current_url_after = browser.current_url
            log_operation("check_and_handle_error_page", "INFO", f"URL after refresh: {current_url_after}")
            
            # Detect page type (without refreshing again, since we already refreshed)
            page_type = 'unknown'
            page_number = None
            
            # Check page type based on URL and page content
            if "OnlineHome.aspx" in current_url_after:
                page_type = 'homepage'
                log_operation("check_and_handle_error_page", "INFO", "Detected: Homepage")
            elif "VisaTypeDetails.aspx" in current_url_after:
                page_type = 'form_page'
                log_operation("check_and_handle_error_page", "INFO", "Detected: Form page")
                # Try to detect page number
                try:
                    # Check for Page 1 fields
                    country_dropdown = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                    if country_dropdown:
                        page_number = 1
                        log_operation("check_and_handle_error_page", "INFO", "Detected: Page 1")
                except:
                    pass
                
                if page_number is None:
                    try:
                        # Check for Page 2 fields
                        surname_input = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtSurname")
                        if surname_input:
                            page_number = 2
                            log_operation("check_and_handle_error_page", "INFO", "Detected: Page 2")
                    except:
                        pass
                
                if page_number is None:
                    try:
                        # Check for Page 3/4 fields
                        page_source_check = browser.page_source
                        if "No Of Years" in page_source_check or "permission to return" in page_source_check:
                            page_number = 3
                            log_operation("check_and_handle_error_page", "INFO", "Detected: Page 3")
                        elif "Date of Issue" in page_source_check or "Is this your first Passport" in page_source_check:
                            page_number = 4
                            log_operation("check_and_handle_error_page", "INFO", "Detected: Page 4")
                    except:
                        pass
            elif "OnlineHome2.aspx" in current_url_after:
                page_type = 'intermediate_page'
                log_operation("check_and_handle_error_page", "INFO", "Detected: Intermediate page")
            
            log_operation("check_and_handle_error_page", "INFO", f"Detected page type: {page_type}, page number: {page_number}")
            
            # Handle based on page type
            if page_type == 'homepage':
                log_operation("check_and_handle_error_page", "INFO", "After error refresh, redirected to homepage - returning homepage_redirect")
                return "homepage_redirect"
            elif page_type == 'form_page':
                log_operation("check_and_handle_error_page", "INFO", f"After error refresh, on form page {page_number} - error resolved, continuing")
                # Error is resolved and we're on form page, return False to continue
                return False
            elif page_type == 'intermediate_page' or "OnlineHome2.aspx" in current_url_after:
                log_operation("check_and_handle_error_page", "INFO", "After error refresh, on intermediate page - attempting to handle")
                # Try to handle intermediate page
                if handle_intermediate_page(browser, wait):
                    log_operation("check_and_handle_error_page", "INFO", "Successfully handled intermediate page after error")
                    # Check final URL after handling intermediate page
                    final_url = browser.current_url
                    if "VisaTypeDetails.aspx" in final_url:
                        log_operation("check_and_handle_error_page", "INFO", "After handling intermediate page, on form page - error resolved, continuing")
                        return False
                    elif "OnlineHome.aspx" in final_url:
                        log_operation("check_and_handle_error_page", "INFO", "After handling intermediate page, redirected to homepage")
                        return "homepage_redirect"
                    else:
                        log_operation("check_and_handle_error_page", "WARN", f"Unexpected URL after handling intermediate page: {final_url}")
                        return "application_error"
                else:
                    log_operation("check_and_handle_error_page", "WARN", "Failed to handle intermediate page after error")
                    return "application_error"
            else:
                log_operation("check_and_handle_error_page", "WARN", f"Unknown page type after error refresh: {page_type}, URL: {current_url_after}")
                # If we can't determine the page type, return application_error to be safe
                return "application_error"
        
        return False  # No error detected
    
    except Exception as e:
        print(f"[WARN] Error checking for error page: {e}")
        return False


def check_application_error(browser, wait):
    """
    Check for application error and return appropriate status.
    This function should be called after any critical operation to detect errors immediately.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        str or None:
            - "application_error" if application error detected (should stop all operations)
            - None if no error detected
    """
    try:
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "application_error":
            return "application_error"
        return None
    except Exception as e:
        print(f"[WARN] Error checking for application error: {e}")
        return None


def check_homepage_redirect(browser, wait):
    """
    Check if the current page has redirected to homepage during form filling.
    This should be called periodically during form filling to detect early redirects.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        str: "homepage" if redirected to homepage, None otherwise
    """
    try:
        current_url = browser.current_url
        if "OnlineHome.aspx" in current_url:
            log_operation("check_homepage_redirect", "WARN", f"Detected redirect to homepage during form filling! URL: {current_url}")
            return "homepage"
        return None
    except Exception as e:
        log_operation("check_homepage_redirect", "WARN", f"Error checking homepage redirect: {e}")
        return None



def check_page_redirect_after_field_fill(browser, wait, field_name, initial_url=None):
    """
    Comprehensive page redirect detection after filling a field.
    This function checks for:
    1. Homepage redirect
    2. Error page
    3. URL changes (indicating page navigation)
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        field_name: Name of the field that was just filled (for logging)
        initial_url: Initial URL before filling the field (optional, for URL change detection)
    
    Returns:
        str or None: 
            - "homepage_redirect" if redirected to homepage
            - "application_error" if application error detected
            - "form_page_X" if redirected to another form page
            - None if no redirect detected
    """
    try:
        # Check for homepage redirect
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation(field_name, "WARN", f"Page redirected to homepage after filling {field_name}, stopping...")
            return "homepage_redirect"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation(field_name, "WARN", f"Error page detected after filling {field_name}, redirected to homepage, stopping...")
            return "homepage_redirect"
        elif error_result == "application_error":
            log_operation(field_name, "ERROR", f"Application error detected after filling {field_name}, stopping...")
            return "application_error"
        elif isinstance(error_result, str) and error_result.startswith("form_page_"):
            log_operation(field_name, "INFO", f"Page redirected to {error_result} after filling {field_name}, stopping...")
            return error_result
        
        # Check if URL changed (indicating page navigation)
        if initial_url:
            current_url_after = browser.current_url
            if current_url_after != initial_url:
                # First check if URL changed to error page
                if "ApplicationError.aspx" in current_url_after or "Error.aspx" in current_url_after:
                    log_operation(field_name, "WARN", f"Page URL changed to error page after filling {field_name}: {current_url_after}, handling error page...")
                    error_result = check_and_handle_error_page(browser, wait)
                    if error_result == "homepage_redirect":
                        return "homepage_redirect"
                    elif error_result == "application_error":
                        return "application_error"
                    elif isinstance(error_result, str) and error_result.startswith("form_page_"):
                        return error_result
                    else:
                        # If error page handling didn't return a clear result, return application_error
                        return "application_error"
                
                # Check if URL changed to a different form page or other page
                # Allow same form page URLs (all pages 1-10)
                # Check if URL is still a form page URL
                is_form_page_url = (
                    "VisaTypeDetails.aspx" in current_url_after or
                    "ApplicantPersonalDetails.aspx" in current_url_after or
                    "GeneralApplicantInfo.aspx" in current_url_after or
                    "ApplicantPassportDetails.aspx" in current_url_after or
                    "EmploymentCollegeDetails.aspx" in current_url_after or
                    "ApplicantEmploymentDetails.aspx" in current_url_after or
                    "TravellingCompanion.aspx" in current_url_after or
                    "ApplicantTravelDetails.aspx" in current_url_after or
                    "ContactHostInfo.aspx" in current_url_after or
                    "ApplicantContactDetails.aspx" in current_url_after or
                    "ContactDetails.aspx" in current_url_after or
                    "ApplicantFamilyDetails.aspx" in current_url_after or
                    "StudentVisa.aspx" in current_url_after or
                    "FormAssistance.aspx" in current_url_after or
                    ("Applicant" in current_url_after and ".aspx" in current_url_after and "ApplicationError" not in current_url_after and "Error" not in current_url_after) or
                    (("Employment" in current_url_after or "College" in current_url_after) and ".aspx" in current_url_after and "ApplicationError" not in current_url_after and "Error" not in current_url_after) or
                    (("Travelling" in current_url_after or "Companion" in current_url_after) and ".aspx" in current_url_after and "ApplicationError" not in current_url_after and "Error" not in current_url_after) or
                    (("Contact" in current_url_after or "Host" in current_url_after) and ".aspx" in current_url_after and "ApplicationError" not in current_url_after and "Error" not in current_url_after)
                )
                if not is_form_page_url:
                    log_operation(field_name, "WARN", f"Page URL changed after filling {field_name}: {current_url_after} (was {initial_url}), detecting page state...")
                    page_state = detect_current_page_state(browser, wait)
                    if page_state['page_type'] == 'homepage':
                        return "homepage_redirect"
                    elif page_state['page_type'] == 'form_page':
                        return f"form_page_{page_state['page_number']}"
                    elif page_state['page_type'] == 'error_page':
                        error_result = check_and_handle_error_page(browser, wait)
                        if error_result == "homepage_redirect":
                            return "homepage_redirect"
                        elif error_result == "application_error":
                            return "application_error"
                        elif isinstance(error_result, str) and error_result.startswith("form_page_"):
                            return error_result
                        else:
                            # If error page handling didn't return a clear result, return application_error
                            return "application_error"
                    elif page_state['page_type'] == 'unknown':
                        # If page type is unknown, check if it's an error page by URL
                        if "ApplicationError.aspx" in current_url_after or "Error.aspx" in current_url_after:
                            log_operation(field_name, "WARN", f"Unknown page type but URL indicates error page, handling error page...")
                            error_result = check_and_handle_error_page(browser, wait)
                            if error_result == "homepage_redirect":
                                return "homepage_redirect"
                            elif error_result == "application_error":
                                return "application_error"
                            elif isinstance(error_result, str) and error_result.startswith("form_page_"):
                                return error_result
                            else:
                                return "application_error"
                        else:
                            # Unknown page type and not an error page, log warning and return None to continue
                            log_operation(field_name, "WARN", f"Unknown page type detected: {current_url_after}, but continuing...")
                            return None
        
        return None
    except Exception as e:
        log_operation(field_name, "WARN", f"Error checking page redirect after filling {field_name}: {e}")
        return None



def detect_current_page_state(browser, wait):
    """
    Detect the current page state and determine what action to take
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        dict: {
            'page_type': 'homepage' | 'form_page' | 'unknown',
            'page_number': int | None,  # If form_page, which page number
            'action': 'click_continue' | 'fill_page' | 'unknown'
        }
    """
    try:
        log_operation("detect_current_page_state", "INFO", "Detecting current page state...")
        
        # Refresh page first to ensure we have the latest state
        browser.refresh()
        time.sleep(2)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(1)
        
        current_url = browser.current_url
        log_operation("detect_current_page_state", "INFO", f"Current URL: {current_url}")
        
        # Check if on error page
        if "ApplicationError.aspx" in current_url or "Error.aspx" in current_url:
            log_operation("detect_current_page_state", "WARN", "Detected: Error page")
            return {
                'page_type': 'error_page',
                'page_number': None,
                'action': 'handle_error'
            }
        
        # Check if on homepage
        if "OnlineHome.aspx" in current_url:
            log_operation("detect_current_page_state", "INFO", "Detected: Homepage")
            return {
                'page_type': 'homepage',
                'page_number': None,
                'action': 'click_continue'
            }
        
        # Check if on form page - accept all form page URLs (Pages 1-10)
        # Page 1: VisaTypeDetails.aspx
        # Page 2: ApplicantPersonalDetails.aspx
        # Page 3: GeneralApplicantInfo.aspx
        # Page 4: ApplicantPassportDetails.aspx
        # Page 5: EmploymentCollegeDetails.aspx
        # Page 6: TravellingCompanion.aspx
        # Page 7: ContactHostInfo.aspx
        # Page 8: ApplicantFamilyDetails.aspx
        # Page 9: StudentVisa.aspx
        # Page 10: FormAssistance.aspx
        is_form_page = (
            "VisaTypeDetails.aspx" in current_url or
            "ApplicantPersonalDetails.aspx" in current_url or
            "GeneralApplicantInfo.aspx" in current_url or
            "ApplicantPassportDetails.aspx" in current_url or
            "EmploymentCollegeDetails.aspx" in current_url or
            "ApplicantEmploymentDetails.aspx" in current_url or
            "TravellingCompanion.aspx" in current_url or
            "ApplicantTravelDetails.aspx" in current_url or
            "ContactHostInfo.aspx" in current_url or
            "ApplicantContactDetails.aspx" in current_url or
            "ContactDetails.aspx" in current_url or
            "ApplicantFamilyDetails.aspx" in current_url or
            "StudentVisa.aspx" in current_url or
            "FormAssistance.aspx" in current_url or
            # Also accept any URL that contains "Applicant" and ".aspx" (to catch any variations)
            ("Applicant" in current_url and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Employment" or "College" and ".aspx" (to catch page 5 variations)
            (("Employment" in current_url or "College" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Travelling" or "Companion" and ".aspx" (to catch page 6 variations)
            (("Travelling" in current_url or "Companion" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Contact" or "Host" and ".aspx" (to catch page 7 variations)
            (("Contact" in current_url or "Host" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url)
        )
        
        if is_form_page:
            log_operation("detect_current_page_state", "INFO", "Detected: Form page")
            
            # Try to detect which page we're on by looking for specific fields
            page_number = None
            
            # Check for Page 1 fields
            try:
                country_dropdown = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                if country_dropdown:
                    page_number = 1
                    log_operation("detect_current_page_state", "INFO", "Detected: Page 1 (Country Of Nationality field found)")
            except:
                pass
            
            # Check for Page 2 fields
            if page_number is None:
                try:
                    surname_input = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtSurname")
                    if surname_input:
                        page_number = 2
                        log_operation("detect_current_page_state", "INFO", "Detected: Page 2 (Surname field found)")
                except:
                    pass
            
            # Check for Page 3 fields (e.g., "No Of Years" or "permission to return")
            if page_number is None:
                try:
                    # Look for "No Of Years" or "permission to return" text
                    page_source = browser.page_source
                    if "No Of Years" in page_source or "permission to return" in page_source or "exempt from the requirement to provide biometrics" in page_source:
                        page_number = 3
                        log_operation("detect_current_page_state", "INFO", "Detected: Page 3 (residence/permission fields found)")
                except:
                    pass
            
            # Check for Page 4 fields (e.g., "Date of Issue" or "Is this your first Passport")
            if page_number is None:
                try:
                    page_source = browser.page_source
                    if "Date of Issue" in page_source or "Is this your first Passport" in page_source or "Issuing Authority" in page_source:
                        page_number = 4
                        log_operation("detect_current_page_state", "INFO", "Detected: Page 4 (passport details fields found)")
                except:
                    pass
            
            # If we couldn't detect the page number, default to form page
            if page_number is None:
                log_operation("detect_current_page_state", "WARN", "Could not detect specific page number, assuming form page")
                page_number = 0  # Unknown page number
            
            return {
                'page_type': 'form_page',
                'page_number': page_number,
                'action': 'fill_page'
            }
        
        # Unknown page
        log_operation("detect_current_page_state", "WARN", f"Unknown page type: {current_url}")
        return {
            'page_type': 'unknown',
            'page_number': None,
            'action': 'unknown'
        }
        
    except Exception as e:
        log_operation("detect_current_page_state", "ERROR", f"Error detecting page state: {e}")
        return {
            'page_type': 'unknown',
            'page_number': None,
            'action': 'unknown'
        }



def detect_page_number_no_refresh(browser, wait):
    """
    Detect the current page number (1-10) without refreshing the page.
    This is used to detect which page we're on after a refresh or navigation.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        int: Page number (1-10) if detected, None if not on form page or cannot detect
    """
    try:
        current_url = browser.current_url
        log_operation("detect_page_number_no_refresh", "DEBUG", f"Current URL: {current_url}")
        
        # Check if on form page - accept all form page URLs (Pages 1-10)
        # Page 1: VisaTypeDetails.aspx
        # Page 2: ApplicantPersonalDetails.aspx
        # Page 3: GeneralApplicantInfo.aspx
        # Page 4: ApplicantPassportDetails.aspx
        # Page 5: EmploymentCollegeDetails.aspx
        # Page 6: TravellingCompanion.aspx
        # Page 7: ContactHostInfo.aspx
        # Page 8: ApplicantFamilyDetails.aspx
        # Page 9: StudentVisa.aspx
        # Page 10: FormAssistance.aspx
        is_form_page = (
            "VisaTypeDetails.aspx" in current_url or
            "ApplicantPersonalDetails.aspx" in current_url or
            "GeneralApplicantInfo.aspx" in current_url or
            "ApplicantPassportDetails.aspx" in current_url or
            "EmploymentCollegeDetails.aspx" in current_url or
            "ApplicantEmploymentDetails.aspx" in current_url or
            "TravellingCompanion.aspx" in current_url or
            "ApplicantTravelDetails.aspx" in current_url or
            "ContactHostInfo.aspx" in current_url or
            "ApplicantContactDetails.aspx" in current_url or
            "ContactDetails.aspx" in current_url or
            "ApplicantFamilyDetails.aspx" in current_url or
            "StudentVisa.aspx" in current_url or
            "FormAssistance.aspx" in current_url or
            # Also accept any URL that contains "Applicant" and ".aspx" (to catch any variations)
            ("Applicant" in current_url and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Employment" or "College" and ".aspx" (to catch page 5 variations)
            (("Employment" in current_url or "College" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Travelling" or "Companion" and ".aspx" (to catch page 6 variations)
            (("Travelling" in current_url or "Companion" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url) or
            # Also accept any URL that contains "Contact" or "Host" and ".aspx" (to catch page 7 variations)
            (("Contact" in current_url or "Host" in current_url) and ".aspx" in current_url and "ApplicationError" not in current_url and "Error" not in current_url)
        )
        
        if not is_form_page:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Not on form page (URL: {current_url})")
            return None
        
        log_operation("detect_page_number_no_refresh", "DEBUG", "On form page, detecting page number...")
        
        # Quick check: If URL contains FormAssistance.aspx, it's likely Page 10
        if "FormAssistance.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains FormAssistance.aspx, likely Page 10")
            # Verify by checking for Page 10 specific content
            try:
                page_source = browser.page_source
                if "Did you receive any assistance" in page_source or "assistance in completing this form" in page_source or "agent/agency" in page_source.lower():
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 10 by URL and content")
                    return 10
            except:
                # Even if content check fails, if URL is FormAssistance.aspx, it's likely Page 10
                log_operation("detect_page_number_no_refresh", "INFO", "URL is FormAssistance.aspx, assuming Page 10")
                return 10
        
        # Quick check: If URL contains StudentVisa.aspx, it's likely Page 9
        if "StudentVisa.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains StudentVisa.aspx, likely Page 9")
            # Verify by checking for Page 9 specific content
            try:
                page_source = browser.page_source
                if "Have you been accepted on a course of study" in page_source or "Course of Study in Ireland" in page_source or "Name of College" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 9 by URL and content")
                    return 9
            except:
                # Even if content check fails, if URL is StudentVisa.aspx, it's likely Page 9
                log_operation("detect_page_number_no_refresh", "INFO", "URL is StudentVisa.aspx, assuming Page 9")
                return 9
        
        # Quick check: If URL contains ApplicantPassportDetails.aspx, it's likely Page 4
        if "ApplicantPassportDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains ApplicantPassportDetails.aspx, likely Page 4")
            # Verify by checking for Page 4 specific content
            try:
                page_source = browser.page_source
                if "Date of Issue" in page_source or "Is this your first Passport" in page_source or "Issuing Authority" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 4 by URL and content")
                    return 4
            except:
                # Even if content check fails, if URL is ApplicantPassportDetails.aspx, it's likely Page 4
                log_operation("detect_page_number_no_refresh", "INFO", "URL is ApplicantPassportDetails.aspx, assuming Page 4")
                return 4
        
        # Quick check: If URL contains EmploymentCollegeDetails.aspx, it's likely Page 5
        if "EmploymentCollegeDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains EmploymentCollegeDetails.aspx, likely Page 5")
            # Verify by checking for Page 5 specific content
            try:
                page_source = browser.page_source
                if "Are you currently employed" in page_source or "Are you currently a student" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 5 by URL and content")
                    return 5
            except:
                # Even if content check fails, if URL is EmploymentCollegeDetails.aspx, it's likely Page 5
                log_operation("detect_page_number_no_refresh", "INFO", "URL is EmploymentCollegeDetails.aspx, assuming Page 5")
                return 5
        
        # Quick check: If URL contains ApplicantEmploymentDetails.aspx, it's likely Page 5
        if "ApplicantEmploymentDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains ApplicantEmploymentDetails.aspx, likely Page 5")
            # Verify by checking for Page 5 specific content
            try:
                page_source = browser.page_source
                if "Are you currently employed" in page_source or "Are you currently a student" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 5 by URL and content")
                    return 5
            except:
                # Even if content check fails, if URL is ApplicantEmploymentDetails.aspx, it's likely Page 5
                log_operation("detect_page_number_no_refresh", "INFO", "URL is ApplicantEmploymentDetails.aspx, assuming Page 5")
                return 5
        
        # Quick check: If URL contains TravellingCompanion.aspx, it's likely Page 6
        if "TravellingCompanion.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains TravellingCompanion.aspx, likely Page 6")
            # Verify by checking for Page 6 specific content
            try:
                page_source = browser.page_source
                if "Will you be travelling with any other person" in page_source or "travelling with any other person" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 6 by URL and content")
                    return 6
            except:
                # Even if content check fails, if URL is TravellingCompanion.aspx, it's likely Page 6
                log_operation("detect_page_number_no_refresh", "INFO", "URL is TravellingCompanion.aspx, assuming Page 6")
                return 6
        
        # Quick check: If URL contains ApplicantTravelDetails.aspx, it's likely Page 6
        if "ApplicantTravelDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains ApplicantTravelDetails.aspx, likely Page 6")
            # Verify by checking for Page 6 specific content
            try:
                page_source = browser.page_source
                if "Will you be travelling with any other person" in page_source or "travelling with any other person" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 6 by URL and content")
                    return 6
            except:
                # Even if content check fails, if URL is ApplicantTravelDetails.aspx, it's likely Page 6
                log_operation("detect_page_number_no_refresh", "INFO", "URL is ApplicantTravelDetails.aspx, assuming Page 6")
                return 6
        
        # Quick check: If URL contains ContactHostInfo.aspx, it's likely Page 7
        if "ContactHostInfo.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains ContactHostInfo.aspx, likely Page 7")
            # Verify by checking for Page 7 specific content
            try:
                page_source = browser.page_source
                if "Is the contact/host in Ireland personally known" in page_source or "contact/host in Ireland" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 7 by URL and content")
                    return 7
            except:
                # Even if content check fails, if URL is ContactHostInfo.aspx, it's likely Page 7
                log_operation("detect_page_number_no_refresh", "INFO", "URL is ContactHostInfo.aspx, assuming Page 7")
                return 7
        
        # Quick check: If URL contains ApplicantContactDetails.aspx or ContactDetails.aspx, it's likely Page 7
        if "ApplicantContactDetails.aspx" in current_url or "ContactDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains contact details page, likely Page 7")
            # Verify by checking for Page 7 specific content
            try:
                page_source = browser.page_source
                if "Is the contact/host in Ireland personally known" in page_source or "contact/host in Ireland" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 7 by URL and content")
                    return 7
            except:
                # Even if content check fails, if URL is contact details page, it's likely Page 7
                log_operation("detect_page_number_no_refresh", "INFO", "URL is contact details page, assuming Page 7")
                return 7
        
        # Quick check: If URL contains ApplicantFamilyDetails.aspx, it's likely Page 8
        if "ApplicantFamilyDetails.aspx" in current_url:
            log_operation("detect_page_number_no_refresh", "INFO", "URL contains ApplicantFamilyDetails.aspx, likely Page 8")
            # Verify by checking for Page 8 specific content
            try:
                page_source = browser.page_source
                if "Personal Status" in page_source or "How many dependant children" in page_source or "How many dependant children do you have" in page_source:
                    log_operation("detect_page_number_no_refresh", "SUCCESS", "Confirmed Page 8 by URL and content")
                    return 8
            except:
                # Even if content check fails, if URL is ApplicantFamilyDetails.aspx, it's likely Page 8
                log_operation("detect_page_number_no_refresh", "INFO", "URL is ApplicantFamilyDetails.aspx, assuming Page 8")
                return 8
        
        # Check for Page 1 fields
        try:
            country_dropdown = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
            if country_dropdown:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 1 field: Country Of Nationality")
                return 1
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 1: {e}")
            pass
        
        # Check for Page 2 fields
        try:
            surname_input = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtSurname")
            if surname_input:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 2 field: Surname")
                return 2
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 2: {e}")
            pass
        
        # Check for Page 3 fields
        try:
            page_source = browser.page_source
            if "No Of Years" in page_source or "permission to return" in page_source or "exempt from the requirement to provide biometrics" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 3 content in page source")
                return 3
            else:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Page 3 keywords not found in page source")
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 3: {e}")
            pass
        
        # Check for Page 4 fields
        try:
            page_source = browser.page_source
            if "Date of Issue" in page_source or "Is this your first Passport" in page_source or "Issuing Authority" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 4 content in page source")
                return 4
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 4: {e}")
            pass
        
        # Check for Page 5 fields
        try:
            page_source = browser.page_source
            if "Are you currently employed" in page_source or "Are you currently a student" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 5 content in page source")
                return 5
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 5: {e}")
            pass
        
        # Check for Page 6 fields
        try:
            page_source = browser.page_source
            if "Will you be travelling with any other person" in page_source or "travelling with any other person" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 6 content in page source")
                return 6
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 6: {e}")
            pass
        
        # Check for Page 7 fields
        try:
            page_source = browser.page_source
            if "Is the contact/host in Ireland personally known" in page_source or "contact/host in Ireland" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 7 content in page source")
                return 7
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 7: {e}")
            pass
        
        # Check for Page 8 fields
        try:
            page_source = browser.page_source
            if "Personal Status" in page_source or "How many dependant children" in page_source or "How many dependant children do you have" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 8 content in page source")
                return 8
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 8: {e}")
            pass
        
        # Check for Page 9 fields
        try:
            page_source = browser.page_source
            if "Have you been accepted on a course of study" in page_source or "Course of Study in Ireland" in page_source or "Name of College" in page_source:
                log_operation("detect_page_number_no_refresh", "DEBUG", "Found Page 9 content in page source")
                return 9
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 9: {e}")
            pass
        
        # Check for Page 10 fields
        try:
            page_source = browser.page_source
            if "Did you receive any assistance" in page_source or "assistance in completing this form" in page_source or "agent/agency" in page_source.lower():
                log_operation("detect_page_number_no_refresh", "SUCCESS", "Detected Page 10 by content (assistance field)")
                return 10
        except Exception as e:
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Error checking Page 10: {e}")
            pass
        
        # If we're on a form page URL but couldn't detect the page number, log more details
        log_operation("detect_page_number_no_refresh", "WARN", f"Could not detect page number. URL: {current_url}")
        try:
            # Try to get page title for debugging
            page_title = browser.title
            log_operation("detect_page_number_no_refresh", "DEBUG", f"Page title: {page_title}")
            
            # Try to get a sample of page text for debugging
            try:
                page_text = browser.find_element(By.TAG_NAME, "body").text[:500]
                log_operation("detect_page_number_no_refresh", "DEBUG", f"Page text sample (first 500 chars): {page_text}")
            except:
                pass
        except:
            pass
        
        return None
        
    except Exception as e:
        log_operation("detect_page_number_no_refresh", "ERROR", f"Error detecting page number: {e}")
        return None



def handle_intermediate_page(browser, wait):
    """
    Handle the intermediate page (OnlineHome2.aspx) by ticking checkbox and clicking the application form link.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        bool: True if successfully navigated to form page, False otherwise
    """
    try:
        log_operation("handle_intermediate_page", "INFO", "Handling intermediate page (OnlineHome2.aspx)...")
        
        # Wait for page to be ready
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
        except:
            pass
        
        # Step 1: Find and check privacy checkbox
        log_operation("handle_intermediate_page", "INFO", "Looking for privacy checkbox on intermediate page...")
        privacy_checkbox = None
        privacy_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_CheckBoxRead"),
            (By.XPATH, "//input[@type='checkbox' and contains(@id, 'CheckBoxRead')]"),
            (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//preceding::input[@type='checkbox'][1]"),
            (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//following::input[@type='checkbox'][1]"),
            (By.XPATH, "//input[@type='checkbox'][contains(../text(), 'I acknowledge')]"),
        ]
        
        for by, selector in privacy_selectors:
            try:
                privacy_checkbox = browser.find_element(by, selector)
                if privacy_checkbox.is_displayed():
                    log_operation("handle_intermediate_page", "SUCCESS", f"Found privacy checkbox: {by}={selector}")
                    break
            except:
                continue
        
        if privacy_checkbox:
            # Scroll to checkbox
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", privacy_checkbox)
            time.sleep(0.5)
            
            # Check if not already checked
            if not privacy_checkbox.is_selected():
                try:
                    privacy_checkbox.click()
                    log_operation("handle_intermediate_page", "SUCCESS", "Privacy checkbox checked")
                except Exception as e:
                    try:
                        browser.execute_script("arguments[0].click();", privacy_checkbox)
                        log_operation("handle_intermediate_page", "SUCCESS", "Privacy checkbox checked using JavaScript")
                    except Exception as e2:
                        log_operation("handle_intermediate_page", "WARN", f"Could not check privacy checkbox: {e}, {e2}")
                time.sleep(1)
            else:
                log_operation("handle_intermediate_page", "INFO", "Privacy checkbox already checked")
        else:
            log_operation("handle_intermediate_page", "WARN", "Privacy checkbox not found, will try to find application form link anyway")
        
        # Step 2: Find and click "AVATS online application form" button/link
        # According to page_source_continue_not_working.md, this is actually a submit button, not a link
        log_operation("handle_intermediate_page", "INFO", "Looking for 'AVATS online application form' button...")
        application_form_element = None
        
        # First, try to find the submit button (this is the actual element according to the HTML)
        button_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
            (By.XPATH, "//input[@type='submit' and @id='ctl00_ContentPlaceHolder1_applyNow']"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'AVATS Online Application Form')]"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'online application form')]"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'application form')]"),
            (By.XPATH, "//input[@type='submit' and contains(@name, 'applyNow')]"),
        ]
        
        for by, selector in button_selectors:
            try:
                application_form_element = browser.find_element(by, selector)
                if application_form_element.is_displayed():
                    button_value = application_form_element.get_attribute("value") or ""
                    log_operation("handle_intermediate_page", "SUCCESS", f"Found application form button: {by}={selector}, value: {button_value[:50]}")
                    break
            except:
                continue
        
        # If button not found, try to find as a link (fallback)
        if not application_form_element:
            log_operation("handle_intermediate_page", "INFO", "Button not found, trying to find as link...")
            link_selectors = [
                (By.XPATH, "//a[contains(text(), 'AVATS online application form')]"),
                (By.XPATH, "//a[contains(text(), 'online application form')]"),
                (By.XPATH, "//a[contains(text(), 'application form')]"),
                (By.XPATH, "//a[contains(., 'AVATS online application form')]"),
                (By.XPATH, "//a[contains(., 'online application form')]"),
                (By.XPATH, "//a[contains(@href, 'VisaTypeDetails')]"),
                (By.XPATH, "//a[contains(@href, 'application')]"),
                (By.XPATH, "//a[contains(@href, 'form')]"),
            ]
            
            for by, selector in link_selectors:
                try:
                    application_form_element = browser.find_element(by, selector)
                    if application_form_element.is_displayed():
                        link_text = application_form_element.text
                        log_operation("handle_intermediate_page", "SUCCESS", f"Found application form link: {by}={selector}, text: {link_text[:50]}")
                        break
                except:
                    continue
            
            # If still not found, try searching all links
            if not application_form_element:
                try:
                    all_links = browser.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        try:
                            link_text = link.text.lower()
                            link_href = link.get_attribute("href") or ""
                            if ("application" in link_text and "form" in link_text) or "VisaTypeDetails" in link_href:
                                if link.is_displayed():
                                    application_form_element = link
                                    log_operation("handle_intermediate_page", "SUCCESS", f"Found application form link by searching all links: text={link.text[:50]}, href={link_href[:50]}")
                                    break
                        except:
                            continue
                except Exception as e:
                    log_operation("handle_intermediate_page", "WARN", f"Error searching for links: {e}")
        
        if application_form_element:
            # Scroll to element
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", application_form_element)
            time.sleep(0.5)
            
            # Click the element (button or link)
            element_type = "button" if application_form_element.tag_name.lower() == "input" else "link"
            try:
                application_form_element.click()
                log_operation("handle_intermediate_page", "SUCCESS", f"Clicked application form {element_type}")
            except Exception as e:
                try:
                    browser.execute_script("arguments[0].click();", application_form_element)
                    log_operation("handle_intermediate_page", "SUCCESS", f"Clicked application form {element_type} using JavaScript")
                except Exception as e2:
                    ActionChains(browser).move_to_element(application_form_element).click().perform()
                    log_operation("handle_intermediate_page", "SUCCESS", f"Clicked application form {element_type} using ActionChains")
            
            # Wait for navigation
            log_operation("handle_intermediate_page", "INFO", f"Waiting for navigation after clicking application form {element_type}...")
            time.sleep(3)
            
            # Wait for document ready
            try:
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except:
                pass
            
            # Check final URL
            final_check = browser.current_url
            log_operation("handle_intermediate_page", "INFO", f"Final URL after clicking {element_type}: {final_check}")
            
            if "VisaTypeDetails.aspx" in final_check:
                log_operation("handle_intermediate_page", "SUCCESS", "Successfully navigated to form page from intermediate page")
                return True
            elif "OnlineHome.aspx" in final_check:
                log_operation("handle_intermediate_page", "WARN", "Redirected back to homepage after clicking element")
                return False
            else:
                log_operation("handle_intermediate_page", "WARN", f"Still not on form page: {final_check}")
                # Wait a bit more and check again
                time.sleep(3)
                final_check_2 = browser.current_url
                if "VisaTypeDetails.aspx" in final_check_2:
                    log_operation("handle_intermediate_page", "SUCCESS", "Successfully navigated to form page after additional wait")
                    return True
                else:
                    log_operation("handle_intermediate_page", "WARN", f"Still not on form page after additional wait: {final_check_2}")
                    return False
        else:
            log_operation("handle_intermediate_page", "ERROR", "Application form button/link not found on intermediate page")
            return False
            
    except Exception as e:
        log_operation("handle_intermediate_page", "ERROR", f"Error handling intermediate page: {e}")
        import traceback
        traceback.print_exc()
        return False



def restart_from_homepage(browser, wait):
    """
    When detected redirect to homepage from form page, refresh page and restart by clicking Continue button.
    This function should NOT perform any form filling operations.
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    
    Returns:
        bool: True if successfully navigated to form page, False otherwise
    """
    try:
        log_operation("restart_from_homepage", "WARN", "Detected redirect to homepage from form page!")
        log_operation("restart_from_homepage", "INFO", "Refreshing page and restarting from homepage...")
        
        # Refresh the page
        current_url = browser.current_url
        log_operation("restart_from_homepage", "INFO", f"Current URL before refresh: {current_url}")
        
        browser.refresh()
        log_operation("restart_from_homepage", "INFO", "Page refreshed")
        
        # Wait for page to load
        time.sleep(3)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(2)
        
        # Verify we're on homepage
        new_url = browser.current_url
        log_operation("restart_from_homepage", "INFO", f"URL after refresh: {new_url}")
        
        if "OnlineHome.aspx" not in new_url:
            log_operation("restart_from_homepage", "WARN", f"Not on homepage after refresh: {new_url}")
            # Try to navigate to homepage
            try:
                browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                time.sleep(3)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                log_operation("restart_from_homepage", "INFO", "Navigated to homepage")
            except Exception as e:
                log_operation("restart_from_homepage", "ERROR", f"Error navigating to homepage: {e}")
                return False
        
        # Check for saved Application Number before clicking Continue
        # Note: We don't extract from page here, only check saved file
        # Application Number extraction happens in fill_page_4/fill_page_5
        # Lazy import to avoid circular dependency
        from .application_management import get_saved_application_number, retrieve_application
        
        saved_app_number = get_saved_application_number()
        
        app_number_to_use = None
        if saved_app_number:
            app_number_to_use = saved_app_number
            log_operation("restart_from_homepage", "INFO", f"Using saved Application Number: {saved_app_number}")
        
        # If Application Number found, retrieve application instead of clicking Continue
        if app_number_to_use:
            log_operation("restart_from_homepage", "INFO", f"Application Number found: {app_number_to_use}, retrieving application instead of clicking Continue...")
            if retrieve_application(browser, wait, app_number_to_use):
                log_operation("restart_from_homepage", "SUCCESS", "Successfully retrieved application")
                # Wait for page to load
                time.sleep(3)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(2)
                # Check if we're now on form page
                final_url = browser.current_url
                if "VisaTypeDetails.aspx" in final_url:
                    log_operation("restart_from_homepage", "SUCCESS", "After retrieving application, on form page")
                    return True
                elif "OnlineHome2.aspx" in final_url:
                    log_operation("restart_from_homepage", "INFO", "On intermediate page after retrieval, calling handle_intermediate_page...")
                    if handle_intermediate_page(browser, wait):
                        return True
                    else:
                        return False
                else:
                    log_operation("restart_from_homepage", "WARN", f"After retrieving application, on unexpected page: {final_url}")
                    return False
            else:
                log_operation("restart_from_homepage", "WARN", "Failed to retrieve application, will try Continue button instead")
        
        # Find and click Continue button on homepage (only if no Application Number or retrieval failed)
        log_operation("restart_from_homepage", "INFO", "Looking for Continue button on homepage...")
        continue_button_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
            (By.XPATH, "//input[@type='submit' and @value='Continue']"),
            (By.XPATH, "//input[@name='ctl00$ContentPlaceHolder1$applyNow']"),
        ]
        
        continue_button = None
        for by, selector in continue_button_selectors:
            try:
                continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("restart_from_homepage", "SUCCESS", f"Found Continue button: {by}={selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue
        
        if continue_button:
            # Store URL before clicking
            url_before_click = browser.current_url
            log_operation("restart_from_homepage", "INFO", f"URL before Continue click: {url_before_click}")
            
            # Scroll to button to ensure it's visible
            try:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
                time.sleep(0.5)
            except:
                pass
            
            # Click Continue button
            click_success = False
            try:
                continue_button.click()
                log_operation("restart_from_homepage", "SUCCESS", "Clicked Continue button")
                click_success = True
            except Exception as e:
                try:
                    browser.execute_script("arguments[0].click();", continue_button)
                    log_operation("restart_from_homepage", "SUCCESS", "Clicked Continue button using JavaScript")
                    click_success = True
                except Exception as e2:
                    try:
                        ActionChains(browser).move_to_element(continue_button).click().perform()
                        log_operation("restart_from_homepage", "SUCCESS", "Clicked Continue button using ActionChains")
                        click_success = True
                    except Exception as e3:
                        log_operation("restart_from_homepage", "WARN", f"All click methods failed. Last error: {e3}")
            
            if not click_success:
                log_operation("restart_from_homepage", "ERROR", "Failed to click Continue button with all methods")
                return False
            
            # Wait for navigation - use similar logic to auto_fill_inis_form
            log_operation("restart_from_homepage", "INFO", "Waiting for navigation to form page...")
            max_wait = 20  # Wait up to 20 seconds
            start_time = time.time()
            navigated = False
            
            while time.time() - start_time < max_wait:
                try:
                    # Check if URL changed
                    new_url = browser.current_url
                    if new_url != url_before_click:
                        log_operation("restart_from_homepage", "SUCCESS", f"URL changed from {url_before_click} to {new_url}")
                        navigated = True
                        break
                    
                    # Check if page is ready
                    ready_state = browser.execute_script("return document.readyState")
                    if ready_state == "complete":
                        # Check if we're on a different page (even if URL hasn't changed yet)
                        try:
                            # Check for form page elements
                            form_elements = browser.find_elements(By.XPATH, "//input[@id='ctl00_ContentPlaceHolder1_ddlCountryOfNationality']")
                            if form_elements:
                                log_operation("restart_from_homepage", "INFO", "Form page elements detected, page may have loaded")
                                navigated = True
                                break
                        except:
                            pass
                    
                    time.sleep(0.5)  # Check every 0.5 seconds
                except Exception as e:
                    log_operation("restart_from_homepage", "DEBUG", f"Check error: {e}")
                    time.sleep(0.5)
            
            # Wait for document ready after navigation detected
            try:
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                time.sleep(2)  # Additional wait for page to fully load
            except:
                pass
            
            # Check final URL
            final_url = browser.current_url
            log_operation("restart_from_homepage", "INFO", f"Final URL after Continue click: {final_url}")
            
            # If still on homepage after waiting, try retrying
            if "OnlineHome.aspx" in final_url and final_url == url_before_click:
                log_operation("restart_from_homepage", "WARN", "Still on homepage after waiting, will retry clicking Continue button...")
                # Retry clicking Continue button (up to 5 more times)
                max_retries = 5
                for retry_count in range(1, max_retries + 1):
                    try:
                        log_operation("restart_from_homepage", "INFO", f"Retry attempt {retry_count}/{max_retries}: Looking for Continue button...")
                        time.sleep(2)  # Wait a bit before retrying
                        
                        # Wait for page to be ready
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        
                        # Find Continue button again
                        continue_button_retry = None
                        for by, selector in continue_button_selectors:
                            try:
                                continue_button_retry = wait.until(EC.element_to_be_clickable((by, selector)))
                                log_operation("restart_from_homepage", "SUCCESS", f"Found Continue button for retry: {by}={selector}")
                                break
                            except:
                                continue
                        
                        if continue_button_retry:
                            # Scroll to button
                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button_retry)
                            time.sleep(1)
                            
                            # Click button
                            try:
                                continue_button_retry.click()
                                log_operation("restart_from_homepage", "SUCCESS", f"Clicked Continue button (retry {retry_count})")
                            except:
                                browser.execute_script("arguments[0].click();", continue_button_retry)
                                log_operation("restart_from_homepage", "SUCCESS", f"Clicked Continue button using JavaScript (retry {retry_count})")
                            
                            # Wait for navigation
                            time.sleep(5)
                            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                            time.sleep(2)
                            
                            # Check URL after retry
                            retry_url = browser.current_url
                            log_operation("restart_from_homepage", "INFO", f"URL after retry {retry_count}: {retry_url}")
                            
                            if "VisaTypeDetails.aspx" in retry_url:
                                log_operation("restart_from_homepage", "SUCCESS", f"Successfully navigated to form page after retry {retry_count}")
                                return True
                            elif "OnlineHome2.aspx" in retry_url:
                                log_operation("restart_from_homepage", "INFO", f"On intermediate page after retry {retry_count}, calling handle_intermediate_page...")
                                if handle_intermediate_page(browser, wait):
                                    return True
                                else:
                                    continue  # Try next retry
                            elif "OnlineHome.aspx" not in retry_url:
                                # URL changed but not to expected pages, might be an error page
                                log_operation("restart_from_homepage", "WARN", f"Unexpected URL after retry {retry_count}: {retry_url}")
                                break
                    except Exception as e:
                        log_operation("restart_from_homepage", "WARN", f"Error during retry {retry_count}: {e}")
                        continue
                
                # If all retries failed, return False
                final_url_after_retries = browser.current_url
                log_operation("restart_from_homepage", "ERROR", f"Failed to navigate after all retries. Final URL: {final_url_after_retries}")
                return False
            
            # Check if navigated to form page
            if "VisaTypeDetails.aspx" in final_url:
                log_operation("restart_from_homepage", "SUCCESS", "Successfully navigated to form page after restart")
                return True
            elif "OnlineHome2.aspx" in final_url:
                log_operation("restart_from_homepage", "INFO", "On intermediate page, calling handle_intermediate_page function...")
                # Call the dedicated function to handle intermediate page
                if handle_intermediate_page(browser, wait):
                    return True
                else:
                    return False
            else:
                log_operation("restart_from_homepage", "WARN", f"Did not navigate to form page: {final_url}")
                return False
        else:
            log_operation("restart_from_homepage", "ERROR", "Continue button not found on homepage")
            return False
            
    except Exception as e:
        log_operation("restart_from_homepage", "ERROR", f"Error restarting from homepage: {e}")
        import traceback
        traceback.print_exc()
        return False


def click_next_button(browser, wait):
    """
    Click the Save and Continue/Next button to proceed to next page
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
    """
    try:
        log_operation("click_next_button", "INFO", "Looking for 'Save and Continue' button...")
        
        # CRITICAL: Check for homepage redirect BEFORE attempting to find button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("click_next_button", "WARN", "Detected redirect to homepage before clicking button, stopping immediately...")
            return "homepage"
        
        # Verify page state before clicking
        if not verify_page_state(browser, wait, 
                                expected_url_pattern="VisaTypeDetails.aspx",
                                operation_name="click_next_button (before)"):
            log_operation("click_next_button", "WARN", "Page state verification failed, but continuing...")
            
            # If verification failed, check if we're on homepage
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("click_next_button", "WARN", "Detected redirect to homepage during page state verification, stopping immediately...")
                return "homepage"
        
        # Wait a bit before looking for button
        time.sleep(OPERATION_DELAY)
        
        # Check again after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("click_next_button", "WARN", "Detected redirect to homepage after wait, stopping immediately...")
            return "homepage"
        
        extended_wait = WebDriverWait(browser, 15)
        next_selectors = [
            (By.ID, "ctl00_ButtonBar_btnSaveContinue"),  # Primary button ID from page source
            (By.ID, "ctl00_ContentPlaceHolder1_btnSaveContinue"),
            (By.XPATH, "//input[@type='submit' and (contains(@value, 'Save and Continue') or contains(@value, 'save and continue') or contains(@value, 'Save & Continue'))]"),
            (By.XPATH, "//input[@type='button' and (contains(@value, 'Save and Continue') or contains(@value, 'save and continue') or contains(@value, 'Save & Continue'))]"),
            (By.XPATH, "//button[contains(text(), 'Save and Continue') or contains(text(), 'save and continue') or contains(text(), 'Save & Continue')]"),
            (By.XPATH, "//input[@type='submit' and (@value='Next' or @value='Continue' or contains(@value, 'Next'))]"),
            (By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Continue')]"),
            (By.XPATH, "//input[@type='button' and (@value='Next' or @value='Continue')]"),
            (By.ID, "ctl00_MainContent_btnNext"),
            (By.ID, "ctl00_MainContent_btnSaveAndContinue"),
            (By.ID, "btnNext"),
            (By.ID, "btnContinue"),
            (By.ID, "btnSaveAndContinue"),
        ]
        
        next_button = None
        for by, selector in next_selectors:
            try:
                next_button = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("click_next_button", "SUCCESS", f"Found 'Save and Continue' button: {by}={selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue
        
        if next_button:
            # Record current URL before clicking
            current_url_before = browser.current_url
            log_operation("click_next_button", "INFO", f"Current URL before clicking: {current_url_before}")
            
            # Scroll to button
            try:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
            except:
                try:
                    browser.execute_script("arguments[0].scrollIntoView(true);", next_button)
                except:
                    ActionChains(browser).move_to_element(next_button).perform()
            time.sleep(0.5)
            
            # Click the button
            try:
                next_button.click()
                log_operation("click_next_button", "SUCCESS", "Clicked 'Save and Continue' button")
            except Exception as click_error:
                try:
                    browser.execute_script("arguments[0].click();", next_button)
                    log_operation("click_next_button", "SUCCESS", "Clicked 'Save and Continue' button using JavaScript")
                except Exception as js_error:
                    try:
                        ActionChains(browser).move_to_element(next_button).click().perform()
                        log_operation("click_next_button", "SUCCESS", "Clicked 'Save and Continue' button using ActionChains")
                    except Exception as ac_error:
                        log_operation("click_next_button", "ERROR", f"Failed to click button with all methods: {click_error}, {js_error}, {ac_error}")
                        return
            
            # Wait for navigation to next page
            log_operation("click_next_button", "INFO", "Waiting for navigation to next page...")
            time.sleep(2)  # Initial wait for page to start loading
            
            # Check for homepage redirect immediately after initial wait
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("click_next_button", "WARN", "Detected redirect to homepage immediately after clicking button, stopping...")
                return "homepage"
            
            # Wait for document ready state
            try:
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except TimeoutException:
                log_operation("click_next_button", "WARN", "Document ready state timeout, but continuing...")
            
            # Check for homepage redirect after document ready
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("click_next_button", "WARN", "Detected redirect to homepage after document ready, stopping...")
                return "homepage"
            
            # Check if URL changed (indicating navigation)
            max_wait = 20
            start_time = time.time()
            navigated = False
            
            while time.time() - start_time < max_wait:
                try:
                    new_url = browser.current_url
                    ready_state = browser.execute_script("return document.readyState")
                    
                    # CRITICAL: Check for error page first
                    if "ApplicationError.aspx" in new_url or "Error.aspx" in new_url:
                        log_operation("click_next_button", "ERROR", f"Detected error page URL during navigation wait: {new_url}, returning application_error")
                        error_result = check_and_handle_error_page(browser, wait)
                        if error_result == "application_error":
                            return "application_error"
                        # If error was handled, check URL again
                        new_url_after = browser.current_url
                        if "ApplicationError.aspx" in new_url_after or "Error.aspx" in new_url_after:
                            return "application_error"
                        new_url = new_url_after
                    
                    # Check for homepage redirect in the loop
                    if "OnlineHome.aspx" in new_url:
                        log_operation("click_next_button", "WARN", "Redirected to homepage during navigation wait, stopping immediately...")
                        # Check for error page
                        check_and_handle_error_page(browser, wait)
                        return "homepage"
                    
                    if new_url != current_url_before:
                        log_operation("click_next_button", "INFO", f"URL changed to: {new_url}")
                        
                        # CRITICAL: Check for error page before considering navigation successful
                        if "ApplicationError.aspx" in new_url or "Error.aspx" in new_url:
                            log_operation("click_next_button", "ERROR", f"Detected error page URL after URL change: {new_url}, returning application_error")
                            error_result = check_and_handle_error_page(browser, wait)
                            if error_result == "application_error":
                                return "application_error"
                            # If error was handled, continue checking
                            new_url = browser.current_url
                            if "ApplicationError.aspx" in new_url or "Error.aspx" in new_url:
                                return "application_error"
                        
                        # Check if we're on a different page (not homepage and not error page)
                        if "VisaTypeDetails.aspx" not in new_url and "OnlineHome.aspx" not in new_url and "ApplicationError.aspx" not in new_url and "Error.aspx" not in new_url:
                            log_operation("click_next_button", "SUCCESS", "Navigated to next page successfully")
                            navigated = True
                            break
                        elif "OnlineHome.aspx" in new_url:
                            log_operation("click_next_button", "WARN", "Redirected to homepage after clicking button")
                            # Check for error page
                            check_and_handle_error_page(browser, wait)
                            return "homepage"
                        elif "VisaTypeDetails.aspx" in new_url:
                            # Still on form page, might be same page or validation error
                            log_operation("click_next_button", "INFO", "Still on form page, may be validation error or same page")
                    
                    if ready_state == "complete":
                        time.sleep(1)
                        final_check = browser.current_url
                        # Check for homepage redirect before checking navigation
                        if "OnlineHome.aspx" in final_check:
                            log_operation("click_next_button", "WARN", "Redirected to homepage after document ready, stopping immediately...")
                            return "homepage"
                        if final_check != current_url_before:
                            log_operation("click_next_button", "SUCCESS", "Page navigation detected after document ready")
                            navigated = True
                            break
                    
                    time.sleep(0.5)
                except Exception as e:
                    log_operation("click_next_button", "DEBUG", f"Error checking navigation: {e}")
                    time.sleep(0.5)
            
            if not navigated:
                log_operation("click_next_button", "WARN", "Navigation not detected, but continuing...")
            
            # Additional wait for page to fully load
            time.sleep(2)
            
            # Verify final page state BEFORE checking error page
            final_url = browser.current_url
            log_operation("click_next_button", "INFO", f"Final URL after navigation: {final_url}")
            
            # CRITICAL: Check for ApplicationError.aspx URL first
            if "ApplicationError.aspx" in final_url or "Error.aspx" in final_url:
                log_operation("click_next_button", "ERROR", f"Detected error page URL: {final_url}, returning application_error")
                # Check and handle error page (which will try to refresh and recover)
                error_result = check_and_handle_error_page(browser, wait)
                if error_result == "application_error":
                    log_operation("click_next_button", "ERROR", "Error page confirmed, returning application_error")
                    return "application_error"
                # If error was handled (e.g., refreshed and recovered), check URL again
                final_url_after = browser.current_url
                if "ApplicationError.aspx" in final_url_after or "Error.aspx" in final_url_after:
                    log_operation("click_next_button", "ERROR", "Still on error page after handling, returning application_error")
                    return "application_error"
                # If recovered, update final_url for further checks
                final_url = final_url_after
            
            # Check for error page after navigation (if not already checked above)
            if "ApplicationError.aspx" not in final_url and "Error.aspx" not in final_url:
                error_result = check_and_handle_error_page(browser, wait)
                if error_result == "application_error":
                    log_operation("click_next_button", "ERROR", "Error page detected by check_and_handle_error_page, returning application_error")
                    return "application_error"
                elif error_result == "homepage_redirect":
                    log_operation("click_next_button", "WARN", "Error page redirected to homepage")
                    return "homepage"
                # Re-check URL after error page handling
                final_url = browser.current_url
                if "ApplicationError.aspx" in final_url or "Error.aspx" in final_url:
                    log_operation("click_next_button", "ERROR", f"Still on error page after error handling: {final_url}, returning application_error")
                    return "application_error"
            
            if "OnlineHome.aspx" in final_url:
                log_operation("click_next_button", "WARN", "Ended up on homepage, may need to restart form filling")
                # Add debugging information to understand why redirect happened
                try:
                    # Check for validation errors or messages on the page
                    page_source = browser.page_source
                    if "error" in page_source.lower() or "validation" in page_source.lower():
                        log_operation("click_next_button", "DEBUG", "Page source contains 'error' or 'validation' keywords - may be validation issue")
                    # Check for session timeout indicators
                    if "session" in page_source.lower() or "timeout" in page_source.lower() or "expired" in page_source.lower():
                        log_operation("click_next_button", "DEBUG", "Page source contains 'session', 'timeout', or 'expired' keywords - may be session issue")
                    # Check page title
                    page_title = browser.title
                    log_operation("click_next_button", "DEBUG", f"Page title: {page_title}")
                except Exception as debug_error:
                    log_operation("click_next_button", "WARN", f"Error during debugging: {debug_error}")
                return "homepage"
            elif "VisaTypeDetails.aspx" in final_url:
                log_operation("click_next_button", "INFO", "Still on form page, may be validation error or same page")
                return "same_page"
            elif "ApplicationError.aspx" in final_url or "Error.aspx" in final_url:
                log_operation("click_next_button", "ERROR", f"Ended up on error page: {final_url}, returning application_error")
                return "application_error"
            else:
                log_operation("click_next_button", "SUCCESS", "Successfully navigated to next page")
                return "success"
        else:
            log_operation("click_next_button", "WARN", "'Save and Continue' button not found")
            return "button_not_found"
            
    except Exception as e:
        log_operation("click_next_button", "ERROR", f"Error clicking 'Save and Continue' button: {e}")
        import traceback
        traceback.print_exc()
        return "error"
    
    # Default return if no explicit return was made
    return "unknown"  


if __name__ == "__main__":
    # Call the auto-fill form function
    auto_fill_inis_form()
