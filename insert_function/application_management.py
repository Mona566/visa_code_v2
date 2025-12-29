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
from .utils import log_operation, OPERATION_DELAY
from .page_detection import (
    detect_page_number_no_refresh, check_homepage_redirect,
    check_and_handle_error_page, detect_current_page_state, restart_from_homepage
)
from .form_helpers import (
    fill_text_by_label, fill_dropdown_by_label, fill_date_by_label
)

def save_page_source_for_debugging(browser, page_number):
    """
    Save HTML page source to a file for debugging purposes
    
    Args:
        browser: Selenium WebDriver instance
        page_number: Page number (2-9) for filename
    
    Returns:
        str or None: Filename if saved successfully, None otherwise
    """
    # Function kept for compatibility but no longer saves files
    return None



def save_application_number(application_number):
    """
    Save Application Number to file after validation
    
    Args:
        application_number: Application Number to save
    
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        if not application_number:
            log_operation("save_application_number", "WARN", "Application Number is empty, not saving")
            return False
        
        app_number = application_number.strip()
        
        # Validate Application Number: must not be empty, "-", "N/A", or other invalid values
        invalid_values = ["-", "n/a", "na", "", "none", "null"]
        if app_number.lower() in invalid_values:
            log_operation("save_application_number", "WARN", f"Invalid Application Number (not saving): '{app_number}'")
            return False
        
        # Application Number should be at least 4 characters (usually longer)
        if len(app_number) < 4:
            log_operation("save_application_number", "WARN", f"Application Number too short (not saving): '{app_number}'")
            return False
        
        # Save to file
        with open("application_number.txt", "w", encoding="utf-8") as f:
            f.write(app_number)
        log_operation("save_application_number", "INFO", f"Application Number saved to 'application_number.txt': {app_number}")
        return True
    except Exception as e:
        log_operation("save_application_number", "WARN", f"Could not save Application Number to file: {e}")
        return False



def get_saved_application_number():
    """
    Check if there's a saved Application Number in the file
    
    Returns:
        str or None: Application Number if found in file, None otherwise
    """
    try:
        import os
        if os.path.exists("application_number.txt"):
            with open("application_number.txt", "r", encoding="utf-8") as f:
                app_number = f.read().strip()
                # Validate Application Number: must not be empty, "-", "N/A", or other invalid values
                invalid_values = ["-", "n/a", "na", "", "none", "null"]
                if app_number and app_number.lower() not in invalid_values:
                    # Application Number should be at least 4 characters (usually longer)
                    if len(app_number) >= 4:
                        log_operation("get_saved_application_number", "INFO", f"Found saved Application Number: {app_number}")
                        return app_number
                    else:
                        log_operation("get_saved_application_number", "WARN", f"Saved Application Number too short (length: {len(app_number)}), ignoring: {app_number}")
                else:
                    log_operation("get_saved_application_number", "WARN", f"Invalid Application Number in file (ignoring): '{app_number}'")
        return None
    except Exception as e:
        log_operation("get_saved_application_number", "WARN", f"Error reading Application Number file: {e}")
        return None



def extract_application_number(browser, wait, save_debug=True):
    """
    Extract Application Number from the page if it contains "Your unique Application Number is..."
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        save_debug: Whether to save debug page source if Application Number not found (default: True)
    
    Returns:
        str or None: Application Number if found, None otherwise
    """
    try:
        log_operation("extract_application_number", "INFO", "Checking for Application Number on page...")
        
        # Get current URL for debugging
        current_url = browser.current_url
        log_operation("extract_application_number", "DEBUG", f"Current URL: {current_url}")
        
        # Get page source and text
        page_source = browser.page_source
        page_text = ""
        try:
            page_text = browser.find_element(By.TAG_NAME, "body").text
            log_operation("extract_application_number", "DEBUG", f"Page text length: {len(page_text)} characters")
        except Exception as e:
            log_operation("extract_application_number", "DEBUG", f"Could not get page text: {e}")
        
        application_number = None
        found_pattern = None
        
        # Method 0 (NEW): Direct element lookup using ID or class (most reliable)
        # Based on HTML structure: <span id="ctl00_ContentPlaceHolder1_TransactionNumberControl1_lblTransactionNumber" class="TransactionNumberText">81144042</span>
        try:
            log_operation("extract_application_number", "INFO", "Trying direct element lookup for TransactionNumber...")
            
            # Try by ID first (most specific)
            transaction_number_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_TransactionNumberControl1_lblTransactionNumber"),
                (By.CLASS_NAME, "TransactionNumberText"),
                (By.XPATH, "//span[contains(@id, 'TransactionNumber')]"),
                (By.XPATH, "//span[@class='TransactionNumberText']"),
                (By.XPATH, "//*[contains(@id, 'lblTransactionNumber')]"),
                (By.XPATH, "//*[contains(@class, 'TransactionNumberText')]"),
            ]
            
            for by, selector in transaction_number_selectors:
                try:
                    element = browser.find_element(by, selector)
                    if element:
                        element_text = element.text.strip()
                        if element_text:
                            # Validate: should be alphanumeric (may include hyphens) and at least 4 characters
                            # Application number can be: pure numbers (e.g., "81144042"), alphanumeric, or with hyphens
                            if len(element_text) >= 4:
                                # Check if it's a valid application number format (alphanumeric with optional hyphens)
                                if re.match(r'^[A-Z0-9\-]+$', element_text, re.IGNORECASE):
                                    application_number = element_text
                                    log_operation("extract_application_number", "SUCCESS", f"Extracted Application Number using direct element lookup ({by}={selector}): {application_number}")
                                    return application_number
                                else:
                                    log_operation("extract_application_number", "DEBUG", f"Element text '{element_text}' does not match application number format")
                except (NoSuchElementException, TimeoutException):
                    continue
                except Exception as e:
                    log_operation("extract_application_number", "DEBUG", f"Error with selector {by}={selector}: {e}")
                    continue
        except Exception as e:
            log_operation("extract_application_number", "DEBUG", f"Error in direct element lookup: {e}")
        
        # Check for Application Number pattern (for fallback methods)
        application_number_patterns = [
            "Your unique Application Number is",
            "Your unique Application Number is:",
            "Application Number is",
            "Application Number is:",
            "unique Application Number",
            "Application Number",
            "Application No",
            "Application No:",
        ]
        
        # Method 1: Try to find Application Number in page text (fallback if direct lookup failed)
        for pattern in application_number_patterns:
            pattern_found_in_source = pattern.lower() in page_source.lower()
            pattern_found_in_text = pattern.lower() in page_text.lower()
            
            if pattern_found_in_source or pattern_found_in_text:
                found_pattern = pattern
                log_operation("extract_application_number", "INFO", f"Found Application Number pattern: '{pattern}' (in source: {pattern_found_in_source}, in text: {pattern_found_in_text})")
                
                # Try multiple extraction methods
                # Method 1.1: Look for pattern followed by number
                patterns_to_try = [
                    r"Your unique Application Number is[:\s]+([A-Z0-9\-]+)",
                    r"Application Number is[:\s]+([A-Z0-9\-]+)",
                    r"unique Application Number[:\s]+([A-Z0-9\-]+)",
                    r"Application Number[:\s]+([A-Z0-9\-]+)",
                    r"Application No[:\s]+([A-Z0-9\-]+)",
                    r"Application Number[:\s]*([A-Z0-9\-]{6,})",
                    r"Application\s+Number[:\s]*([A-Z0-9\-]{6,})",
                ]
                
                for regex_pattern in patterns_to_try:
                    matches = re.findall(regex_pattern, page_source, re.IGNORECASE)
                    if matches:
                        application_number = matches[0].strip()
                        log_operation("extract_application_number", "SUCCESS", f"Extracted Application Number using regex '{regex_pattern}': {application_number}")
                        return application_number
                
                # Method 1.2: Look for elements containing the pattern
                try:
                    xpath_patterns = [
                        "//*[contains(text(), 'Your unique Application Number')]",
                        "//*[contains(text(), 'Application Number is')]",
                        "//*[contains(text(), 'Application Number')]",
                        "//*[contains(., 'Application Number')]",
                    ]
                    
                    for xpath_pattern in xpath_patterns:
                        elements = browser.find_elements(By.XPATH, xpath_pattern)
                        log_operation("extract_application_number", "DEBUG", f"Found {len(elements)} elements using XPath: {xpath_pattern}")
                        
                        for elem in elements:
                            try:
                                elem_text = elem.text
                                log_operation("extract_application_number", "DEBUG", f"Element text: '{elem_text[:200]}'")
                                
                                # Extract number from text - try multiple patterns
                                number_patterns = [
                                    r'([A-Z0-9\-]{6,})',  # At least 6 alphanumeric characters
                                    r'([A-Z]{2,}[0-9]{4,})',  # Letters followed by numbers
                                    r'([0-9]{4,}[A-Z]{2,})',  # Numbers followed by letters
                                ]
                                
                                for num_pattern in number_patterns:
                                    matches = re.findall(num_pattern, elem_text)
                                    if matches:
                                        # Find the match that looks like an application number
                                        for match in matches:
                                            if len(match) >= 6:  # Application numbers are usually at least 6 characters
                                                # Additional validation: should contain both letters and numbers
                                                has_letters = bool(re.search(r'[A-Z]', match))
                                                has_numbers = bool(re.search(r'[0-9]', match))
                                                if has_letters and has_numbers:
                                                    application_number = match.strip()
                                                    log_operation("extract_application_number", "SUCCESS", f"Extracted Application Number from element: {application_number}")
                                                    return application_number
                            except Exception as e:
                                log_operation("extract_application_number", "DEBUG", f"Error processing element: {e}")
                                continue
                except Exception as e:
                    log_operation("extract_application_number", "DEBUG", f"Error in Method 2: {e}")
                    pass
                
                break
        
        # If pattern found but number not extracted, save debug info
        if found_pattern and not application_number:
            log_operation("extract_application_number", "WARN", f"Found pattern '{found_pattern}' but could not extract Application Number")
        
        if not application_number:
            log_operation("extract_application_number", "INFO", "No Application Number found on page")
            return None
        
        return application_number
        
    except Exception as e:
        log_operation("extract_application_number", "WARN", f"Error extracting Application Number: {e}")
        import traceback
        log_operation("extract_application_number", "DEBUG", f"Traceback: {traceback.format_exc()}")
        return None



def retrieve_application(browser, wait, application_number, passport_number="112223", 
                        country_of_nationality="People's Republic of China", date_of_birth="18/06/1995"):
    """
    Click "Retrieve Application" on homepage and fill in the required fields
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        application_number: Application Number to retrieve
        passport_number: Passport Number (default: "112223")
        country_of_nationality: Country of Nationality (default: "People's Republic of China")
        date_of_birth: Date of Birth in format DD/MM/YYYY (default: "18/06/1995")
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Lazy import to avoid circular dependency
    from .main_flow import fill_application_form
    from .page_fillers import (
        fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
        fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10
    )
    
    try:
        # Validate Application Number before proceeding
        if not application_number:
            log_operation("retrieve_application", "ERROR", "Application Number is empty or None")
            return False
        
        # Check for invalid values
        invalid_values = ["-", "n/a", "na", "", "none", "null"]
        if application_number.lower().strip() in invalid_values:
            log_operation("retrieve_application", "ERROR", f"Invalid Application Number: '{application_number}'")
            return False
        
        # Application Number should be at least 4 characters
        if len(application_number.strip()) < 4:
            log_operation("retrieve_application", "ERROR", f"Application Number too short (length: {len(application_number.strip())}): '{application_number}'")
            return False
        
        log_operation("retrieve_application", "INFO", f"Starting to retrieve application with Application Number: {application_number}")
        
        # Check if we're on homepage
        current_url = browser.current_url
        if "OnlineHome.aspx" not in current_url:
            log_operation("retrieve_application", "WARN", f"Not on homepage, current URL: {current_url}")
            # Try to navigate to homepage
            try:
                browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                time.sleep(3)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            except:
                log_operation("retrieve_application", "ERROR", "Could not navigate to homepage")
                return False
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Step 1: Click "Retrieve Application" link
        log_operation("retrieve_application", "INFO", "Looking for 'Retrieve Application' link...")
        retrieve_link = None
        retrieve_selectors = [
            (By.ID, "ctl00_lnkbtnRetrieveApp"),
            (By.XPATH, "//a[contains(text(), 'Retrieve Application')]"),
            (By.XPATH, "//a[@id='ctl00_lnkbtnRetrieveApp']"),
            (By.LINK_TEXT, "Retrieve Application"),
        ]
        
        for by, selector in retrieve_selectors:
            try:
                retrieve_link = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Retrieve Application link: {by}={selector}")
                break
            except:
                continue
        
        if not retrieve_link:
            log_operation("retrieve_application", "ERROR", "Could not find 'Retrieve Application' link")
            return False
        
        # Click the link - use JavaScript click for __doPostBack links
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", retrieve_link)
        time.sleep(0.5)
        
        # Get current URL before clicking
        url_before = browser.current_url
        log_operation("retrieve_application", "INFO", f"Current URL before clicking: {url_before}")
        
        # Try multiple methods to trigger the link
        clicked = False
        
        # Method 1: Direct __doPostBack call (most reliable for ASP.NET)
        try:
            browser.execute_script("__doPostBack('ctl00$lnkbtnRetrieveApp','');")
            log_operation("retrieve_application", "INFO", "Triggered __doPostBack directly")
            clicked = True
        except Exception as e:
            log_operation("retrieve_application", "DEBUG", f"Direct __doPostBack call failed: {e}")
        
        # Method 2: JavaScript click (if Method 1 didn't work)
        if not clicked:
            try:
                browser.execute_script("arguments[0].click();", retrieve_link)
                log_operation("retrieve_application", "INFO", "Clicked 'Retrieve Application' link using JavaScript")
                clicked = True
            except Exception as e:
                log_operation("retrieve_application", "WARN", f"JavaScript click failed: {e}")
        
        # Method 3: Regular click (fallback)
        if not clicked:
            try:
                retrieve_link.click()
                log_operation("retrieve_application", "INFO", "Clicked 'Retrieve Application' link using regular click")
            except Exception as e:
                log_operation("retrieve_application", "ERROR", f"All click methods failed: {e}")
                return False
        
        # Wait for URL to change or page to load
        try:
            # Wait for URL to change (indicating navigation)
            WebDriverWait(browser, 10).until(
                lambda driver: driver.current_url != url_before
            )
            log_operation("retrieve_application", "SUCCESS", f"URL changed to: {browser.current_url}")
        except:
            log_operation("retrieve_application", "WARN", "URL did not change, waiting for page load...")
        
        # Wait for page to load
        time.sleep(2)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(2)
        
        # Check final URL
        final_url = browser.current_url
        log_operation("retrieve_application", "INFO", f"Final URL after clicking: {final_url}")
        
        # Verify we're on the retrieve application page
        if "OnlineHome2.aspx" in final_url or "Retrieve" in final_url or "ApplicationNumber" in browser.page_source:
            log_operation("retrieve_application", "SUCCESS", "Successfully navigated to Retrieve Application page")
        else:
            log_operation("retrieve_application", "WARN", f"May not have navigated to Retrieve Application page. Current URL: {final_url}")
        
        # Check for homepage redirect before filling fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before filling fields, stopping...")
            return False
        
        # Step 2: Fill Application Number
        log_operation("retrieve_application", "INFO", f"Filling Application Number: {application_number}")
        
        # Check for redirect before filling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before filling Application Number, stopping...")
            return False
        
        app_number_input = None
        app_number_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_txtApplicationNumber"),
            (By.XPATH, "//input[contains(@id, 'ApplicationNumber') or contains(@id, 'Application')]"),
            (By.XPATH, "//input[contains(@name, 'ApplicationNumber') or contains(@name, 'Application')]"),
            (By.XPATH, "//input[@type='text' and contains(@id, 'Application')]"),
        ]
        
        for by, selector in app_number_selectors:
            try:
                app_number_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Application Number input: {by}={selector}")
                break
            except:
                continue
        
        if app_number_input:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", app_number_input)
            time.sleep(0.5)
            app_number_input.clear()
            time.sleep(0.2)
            app_number_input.send_keys(application_number)
            time.sleep(0.3)
            verify_value = app_number_input.get_attribute("value")
            if application_number in verify_value or verify_value == application_number:
                log_operation("retrieve_application", "SUCCESS", f"Filled Application Number: {application_number} (verified: {verify_value})")
            else:
                log_operation("retrieve_application", "WARN", f"Application Number not set correctly. Expected '{application_number}', got '{verify_value}'")
        else:
            # Fallback to label-based method
            fill_text_by_label(browser, wait, "Application Number", application_number)
        
        # Check for redirect after filling Application Number
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage after filling Application Number, stopping...")
            return False
        
        time.sleep(OPERATION_DELAY)
        
        # Step 3: Fill Passport Number
        log_operation("retrieve_application", "INFO", f"Filling Passport Number: {passport_number}")
        
        # Check for redirect before filling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before filling Passport Number, stopping...")
            return False
        passport_input = None
        passport_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_txtPassportNo"),
            (By.XPATH, "//input[contains(@id, 'PassportNo') or contains(@id, 'Passport')]"),
            (By.XPATH, "//input[contains(@name, 'PassportNo') or contains(@name, 'Passport')]"),
            (By.XPATH, "//input[@type='text' and contains(@id, 'Passport')]"),
        ]
        
        for by, selector in passport_selectors:
            try:
                passport_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Passport Number input: {by}={selector}")
                break
            except:
                continue
        
        if passport_input:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", passport_input)
            time.sleep(0.5)
            passport_input.clear()
            time.sleep(0.2)
            passport_input.send_keys(passport_number)
            time.sleep(0.3)
            verify_value = passport_input.get_attribute("value")
            if passport_number in verify_value or verify_value == passport_number:
                log_operation("retrieve_application", "SUCCESS", f"Filled Passport Number: {passport_number} (verified: {verify_value})")
            else:
                log_operation("retrieve_application", "WARN", f"Passport Number not set correctly. Expected '{passport_number}', got '{verify_value}'")
        else:
            # Fallback to label-based method
            fill_text_by_label(browser, wait, "Passport Number", passport_number)
        
        # Check for redirect after filling Passport Number
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage after filling Passport Number, stopping...")
            return False
        
        time.sleep(OPERATION_DELAY)
        
        # Step 4: Fill Country of Nationality (dropdown)
        log_operation("retrieve_application", "INFO", f"Selecting Country of Nationality: {country_of_nationality}")
        
        # Check for redirect before filling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before filling Country of Nationality, stopping...")
            return False
        country_dropdown = None
        country_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_ddlNationality"),  # Correct ID for Retrieve Application page
            (By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality"),  # Fallback for form pages
            (By.XPATH, "//select[contains(@id, 'ddlNationality')]"),  # Retrieve page specific
            (By.XPATH, "//select[contains(@id, 'CountryOfNationality') or contains(@id, 'Country')]"),
            (By.XPATH, "//select[contains(@name, 'Nationality')]"),
        ]
        
        for by, selector in country_selectors:
            try:
                country_dropdown = extended_wait.until(EC.presence_of_element_located((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Country of Nationality dropdown: {by}={selector}")
                break
            except:
                continue
        
        if country_dropdown:
            try:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_dropdown)
                time.sleep(0.5)
                select = Select(country_dropdown)
                
                # Try multiple selection methods
                selected = False
                
                # Method 1: Try exact match
                try:
                    select.select_by_visible_text(country_of_nationality)
                    verify_selection = select.first_selected_option.text
                    if country_of_nationality in verify_selection or verify_selection == country_of_nationality:
                        log_operation("retrieve_application", "SUCCESS", f"Selected Country of Nationality: {country_of_nationality} (verified: {verify_selection})")
                        selected = True
                except Exception as e:
                    log_operation("retrieve_application", "DEBUG", f"Exact match failed: {e}")
                
                # Method 2: Try partial match (e.g., "China" in "People's Republic of China")
                if not selected:
                    try:
                        all_options = select.options
                        target_keywords = ["China", "Chinese", "People's Republic"]
                        for option in all_options:
                            option_text = option.text.strip()
                            # Check if option contains any target keyword
                            if any(keyword.lower() in option_text.lower() for keyword in target_keywords):
                                select.select_by_visible_text(option_text)
                                verify_selection = select.first_selected_option.text
                                log_operation("retrieve_application", "SUCCESS", f"Selected Country of Nationality by partial match: {verify_selection}")
                                selected = True
                                break
                    except Exception as e:
                        log_operation("retrieve_application", "DEBUG", f"Partial match failed: {e}")
                
                # Method 3: Try case-insensitive match
                if not selected:
                    try:
                        all_options = select.options
                        target_lower = country_of_nationality.lower()
                        for option in all_options:
                            option_text = option.text.strip()
                            if target_lower == option_text.lower():
                                select.select_by_visible_text(option_text)
                                verify_selection = select.first_selected_option.text
                                log_operation("retrieve_application", "SUCCESS", f"Selected Country of Nationality by case-insensitive match: {verify_selection}")
                                selected = True
                                break
                    except Exception as e:
                        log_operation("retrieve_application", "DEBUG", f"Case-insensitive match failed: {e}")
                
                # Method 4: List all options for debugging if still not selected
                if not selected:
                    try:
                        all_options = select.options
                        option_texts = [opt.text.strip() for opt in all_options[:20]]  # First 20 options
                        log_operation("retrieve_application", "DEBUG", f"Available Country options (first 20): {option_texts}")
                    except:
                        pass
                    log_operation("retrieve_application", "WARN", f"Could not select Country of Nationality: {country_of_nationality}")
                    # Fallback to label-based method
                    fill_dropdown_by_label(browser, wait, "Country of Nationality", country_of_nationality)
                
                time.sleep(OPERATION_DELAY)
            except Exception as e:
                log_operation("retrieve_application", "WARN", f"Error selecting from dropdown: {e}")
                # Fallback to label-based method
                fill_dropdown_by_label(browser, wait, "Country of Nationality", country_of_nationality)
        else:
            log_operation("retrieve_application", "WARN", "Could not find Country of Nationality dropdown by ID, trying label-based method")
            # Fallback to label-based method
            fill_dropdown_by_label(browser, wait, "Country of Nationality", country_of_nationality)
        
        # Check for redirect after filling Country of Nationality (dropdowns can trigger PostBack)
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage after filling Country of Nationality, stopping...")
            return False
        
        time.sleep(OPERATION_DELAY)
        
        # Step 5: Fill Date of Birth
        log_operation("retrieve_application", "INFO", f"Filling Date of Birth: {date_of_birth}")
        
        # Check for redirect before filling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before filling Date of Birth, stopping...")
            return False
        dob_input = None
        dob_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_txtDateOfBirth"),
            (By.XPATH, "//input[contains(@id, 'DateOfBirth') or contains(@id, 'DOB')]"),
            (By.XPATH, "//input[contains(@name, 'DateOfBirth') or contains(@name, 'DOB')]"),
        ]
        
        for by, selector in dob_selectors:
            try:
                dob_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Date of Birth input: {by}={selector}")
                break
            except:
                continue
        
        if dob_input:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", dob_input)
            time.sleep(0.5)
            dob_input.clear()
            time.sleep(0.2)
            dob_input.send_keys(date_of_birth)
            time.sleep(0.3)
            verify_value = dob_input.get_attribute("value")
            if date_of_birth in verify_value or verify_value == date_of_birth:
                log_operation("retrieve_application", "SUCCESS", f"Filled Date of Birth: {date_of_birth} (verified: {verify_value})")
            else:
                log_operation("retrieve_application", "WARN", f"Date of Birth not set correctly. Expected '{date_of_birth}', got '{verify_value}'")
        else:
            # Fallback to label-based method
            fill_date_by_label(browser, wait, "Date of Birth", "", date_of_birth)
        
        # Check for redirect after filling Date of Birth
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage after filling Date of Birth, stopping...")
            return False
        
        time.sleep(OPERATION_DELAY)
        
        log_operation("retrieve_application", "SUCCESS", "All fields filled successfully for application retrieval")
        
        # Check for redirect before clicking Submit
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage before clicking Submit, stopping...")
            return False
        
        # Step 6: Click Submit button to retrieve application
        log_operation("retrieve_application", "INFO", "Looking for Submit button...")
        submit_button = None
        submit_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_btnRetrieve"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'Retrieve') or contains(@value, 'Submit')]"),
            (By.XPATH, "//input[@type='submit' and contains(@id, 'Retrieve')]"),
            (By.XPATH, "//input[@type='submit' and contains(@name, 'Retrieve')]"),
            (By.XPATH, "//button[contains(text(), 'Retrieve') or contains(text(), 'Submit')]"),
        ]
        
        for by, selector in submit_selectors:
            try:
                submit_button = extended_wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("retrieve_application", "SUCCESS", f"Found Submit button: {by}={selector}")
                break
            except:
                continue
        
        if not submit_button:
            log_operation("retrieve_application", "ERROR", "Could not find Submit button")
            return False
        
        # Get current URL before clicking
        url_before = browser.current_url
        log_operation("retrieve_application", "INFO", f"Current URL before clicking Submit: {url_before}")
        
        # Click the submit button
        try:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
            time.sleep(0.5)
            submit_button.click()
            log_operation("retrieve_application", "SUCCESS", "Clicked Submit button")
        except Exception as e:
            log_operation("retrieve_application", "ERROR", f"Error clicking Submit button: {e}")
            return False
        
        # Wait for page to navigate
        try:
            # Wait for URL to change (indicating navigation)
            WebDriverWait(browser, 15).until(
                lambda driver: driver.current_url != url_before
            )
            log_operation("retrieve_application", "SUCCESS", f"URL changed to: {browser.current_url}")
        except:
            log_operation("retrieve_application", "WARN", "URL did not change, waiting for page load...")
        
        # Wait for page to load
        time.sleep(3)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        time.sleep(2)
        
        # Check if we're on the thank you/submission confirmation page
        current_url_after = browser.current_url
        page_source_after = browser.page_source.lower()
        page_text_after = ""
        try:
            page_text_after = browser.find_element(By.TAG_NAME, "body").text.lower()
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
        
        # Check URL first (CompleteFormSummary.aspx is the submission confirmation page)
        if "CompleteFormSummary.aspx" in current_url_after:
            log_operation("retrieve_application", "SUCCESS", f"Detected submission confirmation page by URL: {current_url_after}")
            is_thank_you_page = True
        else:
            # Check page content
            for keyword in thank_you_keywords:
                if keyword in page_source_after or keyword in page_text_after:
                    is_thank_you_page = True
                    log_operation("retrieve_application", "SUCCESS", f"Detected thank you/submission confirmation page after retrieve (keyword: '{keyword}')")
                    break
        
        if is_thank_you_page:
            log_operation("retrieve_application", "INFO", "Application retrieved successfully. Page will remain on thank you page.")
            
            # Check for Application Number on thank you page
            application_number = extract_application_number(browser, wait)
            if application_number:
                log_operation("retrieve_application", "SUCCESS", f"Application Number detected on thank you page: {application_number}")
                save_application_number(application_number)
            
            # Print success message and wait for user to press Enter
            print("\n" + "="*60)
            print("[SUCCESS] Application has been submitted successfully!")
            print("[INFO] Page will remain on thank you page.")
            print("[INFO] Press Enter to exit and close browser...")
            print("="*60 + "\n")
            
            # Wait for user to press Enter (infinite wait)
            input()
            
            # Return True to indicate successful retrieval (application is already submitted)
            return True
        
        # Check for homepage redirect after page load
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("retrieve_application", "WARN", "Redirected to homepage after submit, re-retrieving application...")
            # Check if we still have application number
            saved_app_number = get_saved_application_number()
            if saved_app_number:
                log_operation("retrieve_application", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                # Recursively call retrieve_application
                return retrieve_application(browser, wait, saved_app_number)
            else:
                log_operation("retrieve_application", "WARN", "No Application Number found for re-retrieval")
                return False
        
        # Check for error page
        final_url = browser.current_url
        if "ApplicationError.aspx" in final_url or "Error" in final_url:
            log_operation("retrieve_application", "ERROR", f"Error page detected after submit: {final_url}")
            error_result = check_and_handle_error_page(browser, wait)
            if error_result == "homepage_redirect":
                log_operation("retrieve_application", "WARN", "Redirected to homepage after error handling, re-retrieving application...")
                # Check if we still have application number
                saved_app_number = get_saved_application_number()
                if saved_app_number:
                    log_operation("retrieve_application", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                    # Recursively call retrieve_application
                    return retrieve_application(browser, wait, saved_app_number)
                else:
                    log_operation("retrieve_application", "WARN", "No Application Number found for re-retrieval")
                    return False
            # Wait again after error handling
            time.sleep(2)
            final_url = browser.current_url
            
            # Check for redirect again after error handling
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("retrieve_application", "WARN", "Redirected to homepage after error handling, re-retrieving application...")
                saved_app_number = get_saved_application_number()
                if saved_app_number:
                    log_operation("retrieve_application", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                    return retrieve_application(browser, wait, saved_app_number)
                else:
                    return False
        
        # Check if redirected to homepage (final check)
        if "OnlineHome.aspx" in final_url:
            log_operation("retrieve_application", "WARN", "Redirected to homepage after submit, re-retrieving application...")
            saved_app_number = get_saved_application_number()
            if saved_app_number:
                log_operation("retrieve_application", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                return retrieve_application(browser, wait, saved_app_number)
            else:
                return False
        
        # Step 7: Detect which page we're on and call corresponding fill function
        log_operation("retrieve_application", "INFO", "Detecting current page number after retrieval...")
        
        # Wait for page to be fully loaded before detection
        time.sleep(3)
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except:
            pass
        time.sleep(2)
        
        # Log current URL and page state for debugging
        current_url_after_retrieval = browser.current_url
        log_operation("retrieve_application", "DEBUG", f"Current URL after retrieval: {current_url_after_retrieval}")
        try:
            page_title = browser.title
            log_operation("retrieve_application", "DEBUG", f"Page title: {page_title}")
        except:
            pass
        
        # Retry detection multiple times
        max_retries = 3
        detected_page = None
        for retry in range(max_retries):
            log_operation("retrieve_application", "DEBUG", f"Attempting page detection (attempt {retry + 1}/{max_retries})...")
            detected_page = detect_page_number_no_refresh(browser, wait)
            if detected_page:
                log_operation("retrieve_application", "SUCCESS", f"Detected page {detected_page} after retrieval (attempt {retry + 1})")
                break
            else:
                if retry < max_retries - 1:
                    log_operation("retrieve_application", "WARN", f"Could not detect page number (attempt {retry + 1}/{max_retries}), retrying...")
                    time.sleep(3)  # Wait longer before retry
                    # Wait for page to be ready
                    try:
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    except:
                        pass
                    time.sleep(2)
                else:
                    log_operation("retrieve_application", "WARN", f"Could not detect page number after {max_retries} attempts")
        
        if detected_page:
            log_operation("retrieve_application", "SUCCESS", f"Detected page {detected_page} after retrieval")
            
            # Map page numbers to their fill functions
            page_fill_functions = {
                1: fill_page_1,
                2: fill_page_2,
                3: fill_page_3,
                4: fill_page_4,
                5: fill_page_5,
                6: fill_page_6,
                7: fill_page_7,
                8: fill_page_8,
                9: fill_page_9,
                10: fill_page_10,
            }
            
            if detected_page in page_fill_functions:
                log_operation("retrieve_application", "INFO", f"Calling fill_page_{detected_page} function...")
                try:
                    # Call the corresponding fill function
                    result = page_fill_functions[detected_page](browser, wait)
                    log_operation("retrieve_application", "INFO", f"fill_page_{detected_page} returned: {result}")
                    
                    # If fill function returned homepage_redirect, re-retrieve application
                    if result == "homepage_redirect":
                        log_operation("retrieve_application", "WARN", f"fill_page_{detected_page} returned homepage_redirect, re-retrieving application...")
                        # Check if we still have application number
                        saved_app_number = get_saved_application_number()
                        if saved_app_number:
                            log_operation("retrieve_application", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                            # Recursively call retrieve_application
                            return retrieve_application(browser, wait, saved_app_number)
                        else:
                            log_operation("retrieve_application", "WARN", "No Application Number found for re-retrieval, calling fill_application_form")
                            fill_application_form(browser, wait)
                    # Handle submission_complete
                    elif result == "submission_complete":
                        log_operation("retrieve_application", "SUCCESS", "Application submission completed successfully!")
                        # fill_page_10 already handled the thank you page and user input, just return
                        return True
                    # If the fill function indicates we should continue, check current page first
                    elif result in ["success", True] or (isinstance(result, str) and "form_page_" in result):
                        # Check if we're still on the same page (indicating fill may not have completed)
                        current_page_after = detect_page_number_no_refresh(browser, wait)
                        if current_page_after == detected_page:
                            log_operation("retrieve_application", "WARN", f"Still on page {detected_page} after fill_page_{detected_page} returned {result}, retrying fill...")
                            # Retry filling the same page
                            result_retry = page_fill_functions[detected_page](browser, wait)
                            if result_retry in ["success", True]:
                                # Check again if we moved to next page
                                current_page_after_retry = detect_page_number_no_refresh(browser, wait)
                                if current_page_after_retry == detected_page:
                                    log_operation("retrieve_application", "WARN", f"Still on page {detected_page} after retry, calling fill_application_form...")
                                    fill_application_form(browser, wait)
                                elif current_page_after_retry and current_page_after_retry > detected_page:
                                    log_operation("retrieve_application", "SUCCESS", f"Moved to page {current_page_after_retry} after retry, continuing with fill_application_form...")
                                    fill_application_form(browser, wait)
                                else:
                                    log_operation("retrieve_application", "INFO", "Continuing with fill_application_form...")
                                    fill_application_form(browser, wait)
                            elif isinstance(result_retry, str) and "form_page_" in result_retry:
                                # Retry returned form_page_X, extract page number
                                try:
                                    retry_page_num = int(result_retry.split("_")[-1])
                                    if retry_page_num == detected_page:
                                        # Still on same page, continue filling from that page directly
                                        log_operation("retrieve_application", "INFO", f"Retry returned {result_retry}, still on page {detected_page}, continuing to fill from page {retry_page_num} directly...")
                                        # Continue filling from the detected page directly, not from fill_application_form
                                        # Build page_fill_functions map
                                        page_fill_functions = {
                                            1: fill_page_1,
                                            2: fill_page_2,
                                            3: fill_page_3,
                                            4: fill_page_4,
                                            5: fill_page_5,
                                            6: fill_page_6,
                                            7: fill_page_7,
                                            8: fill_page_8,
                                            9: fill_page_9,
                                            10: fill_page_10,
                                        }
                                        
                                        # Continue filling from the detected page
                                        current_page = retry_page_num
                                        while current_page <= 10:
                                            if current_page not in page_fill_functions:
                                                break
                                            
                                            log_operation("retrieve_application", "INFO", f"Filling page {current_page}...")
                                            time.sleep(2)
                                            result = page_fill_functions[current_page](browser, wait)
                                            
                                            # Check for application error
                                            if result == "application_error":
                                                log_operation("retrieve_application", "ERROR", f"Application error detected on page {current_page} - stopping")
                                                return False
                                            
                                            # Check for homepage redirect
                                            if result == "homepage_redirect":
                                                saved_app_number = get_saved_application_number()
                                                if saved_app_number:
                                                    log_operation("retrieve_application", "INFO", f"Homepage redirect detected, re-retrieving application with number: {saved_app_number}")
                                                    return retrieve_application(browser, wait, saved_app_number)
                                                else:
                                                    log_operation("retrieve_application", "WARN", "Homepage redirect but no application number, stopping")
                                                    return False
                                            
                                            # Check for page jump
                                            if isinstance(result, str) and "form_page_" in result:
                                                new_page_num = int(result.split("_")[-1])
                                                log_operation("retrieve_application", "INFO", f"Page jump detected: from page {current_page} to page {new_page_num}")
                                                current_page = new_page_num
                                                continue
                                            
                                            # Check for submission complete
                                            if result == "submission_complete":
                                                log_operation("retrieve_application", "SUCCESS", "Application submission completed successfully!")
                                                return True
                                            
                                            # If success, move to next page
                                            if result in ["success", True]:
                                                current_page += 1
                                            else:
                                                # Unexpected result, try to detect current page
                                                detected_current = detect_page_number_no_refresh(browser, wait)
                                                if detected_current and detected_current > current_page:
                                                    log_operation("retrieve_application", "INFO", f"Detected page jump to {detected_current}, continuing from there...")
                                                    current_page = detected_current
                                                else:
                                                    log_operation("retrieve_application", "WARN", f"Unexpected result: {result}, continuing to next page...")
                                                    current_page += 1
                                        
                                        log_operation("retrieve_application", "SUCCESS", "Finished filling all pages from retrieve_application")
                                        return True
                                    elif retry_page_num > detected_page:
                                        # Moved to next page
                                        log_operation("retrieve_application", "SUCCESS", f"Retry returned {result_retry}, moved to page {retry_page_num}, continuing with fill_application_form...")
                                        fill_application_form(browser, wait)
                                    else:
                                        # Moved to previous page (unexpected)
                                        log_operation("retrieve_application", "WARN", f"Retry returned {result_retry}, moved to page {retry_page_num} (previous page), continuing with fill_application_form...")
                                        fill_application_form(browser, wait)
                                except Exception as e:
                                    log_operation("retrieve_application", "WARN", f"Could not parse page number from {result_retry}: {e}, continuing with fill_application_form...")
                                    fill_application_form(browser, wait)
                            else:
                                log_operation("retrieve_application", "WARN", f"Retry returned unexpected result: {result_retry}, continuing with fill_application_form...")
                                fill_application_form(browser, wait)
                        elif current_page_after and current_page_after > detected_page:
                            log_operation("retrieve_application", "SUCCESS", f"Moved to page {current_page_after}, continuing with fill_application_form...")
                            fill_application_form(browser, wait)
                        elif isinstance(result, str) and "form_page_" in result:
                            # Explicitly redirected to another page
                            log_operation("retrieve_application", "INFO", f"Redirected to {result}, continuing with fill_application_form...")
                            fill_application_form(browser, wait)
                        else:
                            log_operation("retrieve_application", "INFO", "Continuing with fill_application_form...")
                            fill_application_form(browser, wait)
                    else:
                        log_operation("retrieve_application", "WARN", f"fill_page_{detected_page} returned unexpected result: {result}, calling fill_application_form")
                        fill_application_form(browser, wait)
                except Exception as e:
                    log_operation("retrieve_application", "ERROR", f"Error calling fill_page_{detected_page}: {e}")
                    # Still try to continue with fill_application_form
                    fill_application_form(browser, wait)
            else:
                log_operation("retrieve_application", "WARN", f"Page {detected_page} not in fill functions map, calling fill_application_form directly")
                fill_application_form(browser, wait)
        else:
            # Could not detect page number after retries
            log_operation("retrieve_application", "WARN", "Could not detect page number after retries, checking for Application Number...")
            
            # Check for saved Application Number
            saved_app_number = get_saved_application_number()
            if saved_app_number:
                log_operation("retrieve_application", "INFO", f"Found Application Number: {saved_app_number}, re-retrieving application...")
                # Re-retrieve application (this will try again to detect the page)
                if retrieve_application(browser, wait, saved_app_number):
                    log_operation("retrieve_application", "SUCCESS", "Successfully re-retrieved application")
                    return True
                else:
                    log_operation("retrieve_application", "WARN", "Failed to re-retrieve application, trying restart_from_homepage...")
                    # If re-retrieval failed, try restart_from_homepage
                    if restart_from_homepage(browser, wait):
                        log_operation("retrieve_application", "INFO", "Successfully restarted from homepage")
                        return True
                    else:
                        log_operation("retrieve_application", "ERROR", "Failed to restart from homepage")
                        return False
            else:
                # No Application Number found, use restart_from_homepage (clicks Continue)
                log_operation("retrieve_application", "INFO", "No Application Number found, using restart_from_homepage (click Continue)...")
                if restart_from_homepage(browser, wait):
                    log_operation("retrieve_application", "INFO", "Successfully restarted from homepage")
                    return True
                else:
                    log_operation("retrieve_application", "ERROR", "Failed to restart from homepage")
                    return False
        
        return True
        
    except Exception as e:
        log_operation("retrieve_application", "ERROR", f"Error retrieving application: {e}")
        import traceback
        traceback.print_exc()
        return False


