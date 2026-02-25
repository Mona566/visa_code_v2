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

def fill_page_3(browser, wait, screenshots_dir=None):
    """
    Fill the third page of the application form
    
    Fields to fill:
    - Length of residence in present country: No Of Years: 33, No Of Months: 6
    - Do you have permission to return to that country after your stay in Ireland?: Yes
    - Are you exempt from the requirement to provide biometrics?: No
    - Have you applied for an Irish Visa/Preclearance before?: No
    - Have you ever been issued with an Irish Visa/Preclearance before?: No
    - Please provide the location, application number and year of issue: N/A
    - Have you ever been refused an Irish Visa/Preclearance?: No
    - If you have been refused before, please provide location of application, year and reference number: N/A
    - Have you ever been in Ireland before?: No
    - Do you have family members living in Ireland?: No
    - Have you ever been refused permission to enter Ireland before?: No
    - Have you ever been notified of a deportation order to leave Ireland?: No
    - Have you ever been refused a visa to another country?: No
    - Have you ever been refused entry to, deported from, overstayed permission in, or were otherwise required to leave any country?: No
    - If yes to any of the above please give details: N/A
    - Have you any criminal convictions in any country?: No
    """
    log_operation("fill_page_3", "INFO", "Starting to fill Page 3...")
    
    try:
        # Record initial URL before filling fields
        initial_url = browser.current_url
        log_operation("fill_page_3", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Already on homepage before starting Page 3, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 3 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_3", "INFO", "Page 3 document ready")
        except:
            log_operation("fill_page_3", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_3", "SUCCESS", f"Application Number detected when entering Page 3: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        extended_wait = WebDriverWait(browser, 15)
        
        # Record initial URL before starting to fill fields
        initial_url = browser.current_url
        log_operation("fill_page_3", "INFO", f"Initial URL before filling fields: {initial_url}")
        
        # 1. Length of residence in present country - No Of Years
        try:
            log_operation("No Of Years", "INFO", "Filling No Of Years field...")
            
            # Check for page redirect before starting to fill
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("No Of Years", "WARN", "Page redirected to homepage before filling No Of Years, stopping...")
                return "homepage_redirect"
            
            # Check if URL changed before starting
            current_url_before = browser.current_url
            if current_url_before != initial_url:
                log_operation("No Of Years", "WARN", f"Page URL changed before filling No Of Years: {current_url_before} (was {initial_url}), detecting page state...")
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
            
            # Save page source for debugging if field not found
            page_source_saved = False
            
            # Try to find as dropdown/select first (most likely)
            years_dropdown = None
            years_dropdown_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_ddlNoOfYears"),
                (By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]"),
                (By.XPATH, "//select[contains(@name, 'NoOfYears') or contains(@name, 'Years')]"),
            ]
            
            for by, selector in years_dropdown_selectors:
                try:
                    years_dropdown = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("No Of Years", "SUCCESS", f"Found years dropdown: {by}={selector}")
                    break
                except:
                    continue
            
            if years_dropdown:
                # It's a dropdown, use Select
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", years_dropdown)
                    time.sleep(0.5)
                    
                    # Check if dropdown has onchange event (indicates PostBack)
                    has_postback = browser.execute_script("""
                        var select = arguments[0];
                        return select.onchange !== null || select.getAttribute('onchange') !== null || 
                               select.getAttribute('data-postback') === 'true';
                    """, years_dropdown)
                    
                    # Record URL before selection
                    url_before_selection = browser.current_url
                    log_operation("No Of Years", "INFO", f"URL before selection: {url_before_selection}, has_postback: {has_postback}")
                    
                    select_years = Select(years_dropdown)
                    # Try to select by visible text "33"
                    try:
                        select_years.select_by_visible_text("33")
                        time.sleep(0.3)
                        
                        # If PostBack detected, wait for it to complete
                        if has_postback:
                            log_operation("No Of Years", "INFO", "PostBack detected, waiting for PostBack to complete...")
                            max_postback_wait = 15
                            postback_start_time = time.time()
                            postback_completed = False
                            
                            while time.time() - postback_start_time < max_postback_wait:
                                try:
                                    current_url_check = browser.current_url
                                    ready_state = browser.execute_script("return document.readyState")
                                    
                                    # Check if URL changed (PostBack completed)
                                    if current_url_check != url_before_selection:
                                        log_operation("No Of Years", "INFO", f"URL changed after PostBack: {current_url_check}")
                                        time.sleep(2)  # Wait for page to fully load
                                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                        time.sleep(1)
                                        postback_completed = True
                                        break
                                    
                                    # Check if page is ready and element still exists
                                    if ready_state == "complete":
                                        try:
                                            # Re-find the dropdown to check if value was saved
                                            years_dropdown_after = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                                            select_years_after = Select(years_dropdown_after)
                                            selected_value_after = select_years_after.first_selected_option.text
                                            if "33" in selected_value_after:
                                                log_operation("No Of Years", "SUCCESS", f"PostBack completed, value saved: {selected_value_after}")
                                                postback_completed = True
                                                break
                                        except:
                                            pass
                                    
                                    time.sleep(0.5)
                                except Exception as e:
                                    log_operation("No Of Years", "DEBUG", f"Error checking PostBack status: {e}")
                                    time.sleep(0.5)
                            
                            if not postback_completed:
                                log_operation("No Of Years", "WARN", "PostBack wait timeout, but continuing...")
                        else:
                            # No PostBack, just verify selection
                            selected_value = select_years.first_selected_option.text
                            if "33" in selected_value:
                                log_operation("No Of Years", "SUCCESS", f"Selected '33' in dropdown (selected: {selected_value})")
                            else:
                                log_operation("No Of Years", "WARN", f"Selected value '{selected_value}' doesn't match '33'")
                    except:
                        # Try selecting by value
                        try:
                            select_years.select_by_value("33")
                            time.sleep(0.3)
                            
                            # If PostBack detected, wait for it to complete
                            if has_postback:
                                log_operation("No Of Years", "INFO", "PostBack detected (value selection), waiting for PostBack to complete...")
                                max_postback_wait = 15
                                postback_start_time = time.time()
                                postback_completed = False
                                
                                while time.time() - postback_start_time < max_postback_wait:
                                    try:
                                        current_url_check = browser.current_url
                                        ready_state = browser.execute_script("return document.readyState")
                                        
                                        if current_url_check != url_before_selection:
                                            log_operation("No Of Years", "INFO", f"URL changed after PostBack: {current_url_check}")
                                            time.sleep(2)
                                            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                            time.sleep(1)
                                            postback_completed = True
                                            break
                                        
                                        if ready_state == "complete":
                                            try:
                                                years_dropdown_after = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                                                select_years_after = Select(years_dropdown_after)
                                                selected_value_after = select_years_after.first_selected_option.text
                                                if "33" in selected_value_after:
                                                    log_operation("No Of Years", "SUCCESS", f"PostBack completed, value saved: {selected_value_after}")
                                                    postback_completed = True
                                                    break
                                            except:
                                                pass
                                        
                                        time.sleep(0.5)
                                    except Exception as e:
                                        log_operation("No Of Years", "DEBUG", f"Error checking PostBack status: {e}")
                                        time.sleep(0.5)
                                
                                if not postback_completed:
                                    log_operation("No Of Years", "WARN", "PostBack wait timeout, but continuing...")
                            else:
                                selected_value = select_years.first_selected_option.text
                                log_operation("No Of Years", "SUCCESS", f"Selected '33' by value (selected: {selected_value})")
                        except:
                            log_operation("No Of Years", "WARN", "Could not select '33' in dropdown")
                except Exception as e:
                    log_operation("No Of Years", "WARN", f"Error selecting from dropdown: {e}")
            else:
                # Try as text input
                years_input = None
                years_input_selectors = [
                    (By.ID, "ctl00_ContentPlaceHolder1_txtNoOfYears"),
                    (By.XPATH, "//input[contains(@id, 'NoOfYears') or contains(@id, 'Years')]"),
                    (By.XPATH, "//input[contains(@name, 'NoOfYears') or contains(@name, 'Years')]"),
                    (By.XPATH, "//input[@type='text' and contains(@id, 'Years')]"),
                ]
                
                for by, selector in years_input_selectors:
                    try:
                        years_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                        log_operation("No Of Years", "SUCCESS", f"Found years input: {by}={selector}")
                        break
                    except:
                        continue
                
                if years_input:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", years_input)
                    time.sleep(0.5)
                    years_input.clear()
                    time.sleep(0.2)
                    years_input.send_keys("33")
                    time.sleep(0.3)
                    # Verify the value was set
                    input_value = years_input.get_attribute("value")
                    if input_value == "33":
                        log_operation("No Of Years", "SUCCESS", f"Filled No Of Years: 33 (verified: {input_value})")
                    else:
                        log_operation("No Of Years", "WARN", f"Value not set correctly. Expected '33', got '{input_value}'")
                else:
                    # Fallback to label-based method with multiple label variations
                    label_variations = ["No Of Years", "Years", "No. Of Years", "Number of Years", "Length of residence"]
                    for label_var in label_variations:
                        try:
                            fill_text_by_label(browser, wait, label_var, "33")
                            time.sleep(0.3)
                            
                            # Check for page redirect immediately after label-based fill
                            redirect_check = check_homepage_redirect(browser, wait)
                            if redirect_check == "homepage":
                                log_operation("No Of Years", "WARN", f"Page redirected to homepage after filling via label '{label_var}', stopping...")
                                return "homepage_redirect"
                            
                            # Check if URL changed
                            current_url_after_label = browser.current_url
                            if current_url_after_label != initial_url:
                                log_operation("No Of Years", "WARN", f"Page URL changed after filling via label '{label_var}': {current_url_after_label}, detecting page state...")
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
                            
                            # Try to verify
                            try:
                                verify_input = browser.find_element(By.XPATH, f"//input[contains(@id, 'Years')]")
                                verify_value = verify_input.get_attribute("value")
                                if verify_value == "33":
                                    log_operation("No Of Years", "SUCCESS", f"Filled using label variation: {label_var} (verified: {verify_value})")
                                    break
                                else:
                                    log_operation("No Of Years", "WARN", f"Filled using label but value not verified. Got: {verify_value}")
                            except:
                                log_operation("No Of Years", "SUCCESS", f"Filled using label variation: {label_var} (could not verify)")
                                break
                        except:
                            continue
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling No Of Years
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("No Of Years", "WARN", "Page redirected to homepage after filling No Of Years, stopping...")
                return "homepage_redirect"
            
            # Check for error page
            error_result = check_and_handle_error_page(browser, wait)
            if error_result == "homepage_redirect":
                log_operation("No Of Years", "WARN", "Error page detected after filling No Of Years, redirected to homepage, stopping...")
                return "homepage_redirect"
            elif error_result == "application_error":
                log_operation("No Of Years", "ERROR", "Application error detected after filling No Of Years, stopping...")
                return "application_error"
            elif isinstance(error_result, str) and error_result.startswith("form_page_"):
                log_operation("No Of Years", "INFO", f"Page redirected to {error_result} after filling No Of Years, stopping...")
                return error_result
            
            # Check if URL changed (indicating page navigation)
            # Allow same form page URLs (e.g., VisaTypeDetails.aspx, ApplicantPersonalDetails.aspx, GeneralApplicantInfo.aspx)
            current_url_after = browser.current_url
            is_form_page_url = (
                "ApplicantPersonalDetails.aspx" in current_url_after or
                "VisaTypeDetails.aspx" in current_url_after or
                "GeneralApplicantInfo.aspx" in current_url_after or
                "StudentVisa.aspx" in current_url_after or
                "ApplicantFamilyDetails.aspx" in current_url_after or
                "ContactDetails.aspx" in current_url_after or
                "FormAssistance.aspx" in current_url_after
            )
            
            if not is_form_page_url:
                log_operation("No Of Years", "WARN", f"Page URL changed to non-form page after filling No Of Years: {current_url_after}, detecting page state...")
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
            elif current_url_after != initial_url and "GeneralApplicantInfo.aspx" in current_url_after:
                # URL changed to GeneralApplicantInfo.aspx (likely PostBack), verify field value was saved
                log_operation("No Of Years", "INFO", f"URL changed to GeneralApplicantInfo.aspx after selection, verifying field value was saved...")
                try:
                    time.sleep(1)  # Wait a bit for page to stabilize
                    years_dropdown_verify = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                    select_years_verify = Select(years_dropdown_verify)
                    selected_value_verify = select_years_verify.first_selected_option.text
                    if "33" in selected_value_verify:
                        log_operation("No Of Years", "SUCCESS", f"Field value verified after PostBack: {selected_value_verify}")
                    else:
                        log_operation("No Of Years", "WARN", f"Field value not saved after PostBack. Expected '33', got '{selected_value_verify}'")
                        # Try to select again
                        log_operation("No Of Years", "INFO", "Retrying selection after PostBack...")
                        select_years_verify.select_by_visible_text("33")
                        time.sleep(0.5)
                        selected_value_retry = select_years_verify.first_selected_option.text
                        if "33" in selected_value_retry:
                            log_operation("No Of Years", "SUCCESS", f"Field value saved after retry: {selected_value_retry}")
                        else:
                            log_operation("No Of Years", "WARN", f"Field value still not saved after retry: {selected_value_retry}")
                except Exception as e:
                    log_operation("No Of Years", "WARN", f"Could not verify field value after PostBack: {e}")
        except Exception as e:
            log_operation("No Of Years", "WARN", f"Error filling No Of Years: {e}")
            import traceback
            traceback.print_exc()
            
            # Check for page redirect even if there was an error
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("No Of Years", "WARN", "Page redirected to homepage after error filling No Of Years, stopping...")
                return "homepage_redirect"
        
        # 2. Length of residence in present country - No Of Months
        try:
            log_operation("No Of Months", "INFO", "Filling No Of Months field...")
            
            # Save page source for debugging if field not found
            page_source_saved = False
            
            # Try to find as dropdown/select first (most likely)
            months_dropdown = None
            months_dropdown_selectors = [
                (By.ID, "ctl00_ContentPlaceHolder1_ddlNoOfMonths"),
                (By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]"),
                (By.XPATH, "//select[contains(@name, 'NoOfMonths') or contains(@name, 'Months')]"),
            ]
            
            for by, selector in months_dropdown_selectors:
                try:
                    months_dropdown = extended_wait.until(EC.presence_of_element_located((by, selector)))
                    log_operation("No Of Months", "SUCCESS", f"Found months dropdown: {by}={selector}")
                    break
                except:
                    continue
            
            if months_dropdown:
                # It's a dropdown, use Select
                try:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", months_dropdown)
                    time.sleep(0.5)
                    
                    # Check if dropdown has onchange event (indicates PostBack)
                    has_postback = browser.execute_script("""
                        var select = arguments[0];
                        return select.onchange !== null || select.getAttribute('onchange') !== null || 
                               select.getAttribute('data-postback') === 'true';
                    """, months_dropdown)
                    
                    # Record URL before selection
                    url_before_selection = browser.current_url
                    log_operation("No Of Months", "INFO", f"URL before selection: {url_before_selection}, has_postback: {has_postback}")
                    
                    select_months = Select(months_dropdown)
                    # Try to select by visible text "6"
                    try:
                        select_months.select_by_visible_text("6")
                        time.sleep(0.3)
                        
                        # If PostBack detected, wait for it to complete
                        if has_postback:
                            log_operation("No Of Months", "INFO", "PostBack detected, waiting for PostBack to complete...")
                            max_postback_wait = 15
                            postback_start_time = time.time()
                            postback_completed = False
                            
                            while time.time() - postback_start_time < max_postback_wait:
                                try:
                                    current_url_check = browser.current_url
                                    ready_state = browser.execute_script("return document.readyState")
                                    
                                    # Check if URL changed (PostBack completed)
                                    if current_url_check != url_before_selection:
                                        log_operation("No Of Months", "INFO", f"URL changed after PostBack: {current_url_check}")
                                        time.sleep(2)  # Wait for page to fully load
                                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                        time.sleep(1)
                                        postback_completed = True
                                        break
                                    
                                    # Check if page is ready and element still exists
                                    if ready_state == "complete":
                                        try:
                                            # Re-find the dropdown to check if value was saved
                                            months_dropdown_after = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                                            select_months_after = Select(months_dropdown_after)
                                            selected_value_after = select_months_after.first_selected_option.text
                                            if "6" in selected_value_after:
                                                log_operation("No Of Months", "SUCCESS", f"PostBack completed, value saved: {selected_value_after}")
                                                postback_completed = True
                                                break
                                        except:
                                            pass
                                    
                                    time.sleep(0.5)
                                except Exception as e:
                                    log_operation("No Of Months", "DEBUG", f"Error checking PostBack status: {e}")
                                    time.sleep(0.5)
                            
                            if not postback_completed:
                                log_operation("No Of Months", "WARN", "PostBack wait timeout, but continuing...")
                        else:
                            # No PostBack, just verify selection
                            selected_value = select_months.first_selected_option.text
                            if "6" in selected_value:
                                log_operation("No Of Months", "SUCCESS", f"Selected '6' in dropdown (selected: {selected_value})")
                            else:
                                log_operation("No Of Months", "WARN", f"Selected value '{selected_value}' doesn't match '6'")
                    except:
                        # Try selecting by value
                        try:
                            select_months.select_by_value("6")
                            time.sleep(0.3)
                            
                            # If PostBack detected, wait for it to complete
                            if has_postback:
                                log_operation("No Of Months", "INFO", "PostBack detected (value selection), waiting for PostBack to complete...")
                                max_postback_wait = 15
                                postback_start_time = time.time()
                                postback_completed = False
                                
                                while time.time() - postback_start_time < max_postback_wait:
                                    try:
                                        current_url_check = browser.current_url
                                        ready_state = browser.execute_script("return document.readyState")
                                        
                                        if current_url_check != url_before_selection:
                                            log_operation("No Of Months", "INFO", f"URL changed after PostBack: {current_url_check}")
                                            time.sleep(2)
                                            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                            time.sleep(1)
                                            postback_completed = True
                                            break
                                        
                                        if ready_state == "complete":
                                            try:
                                                months_dropdown_after = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                                                select_months_after = Select(months_dropdown_after)
                                                selected_value_after = select_months_after.first_selected_option.text
                                                if "6" in selected_value_after:
                                                    log_operation("No Of Months", "SUCCESS", f"PostBack completed, value saved: {selected_value_after}")
                                                    postback_completed = True
                                                    break
                                            except:
                                                pass
                                        
                                        time.sleep(0.5)
                                    except Exception as e:
                                        log_operation("No Of Months", "DEBUG", f"Error checking PostBack status: {e}")
                                        time.sleep(0.5)
                                
                                if not postback_completed:
                                    log_operation("No Of Months", "WARN", "PostBack wait timeout, but continuing...")
                            else:
                                selected_value = select_months.first_selected_option.text
                                log_operation("No Of Months", "SUCCESS", f"Selected '6' by value (selected: {selected_value})")
                        except:
                            log_operation("No Of Months", "WARN", "Could not select '6' in dropdown")
                except Exception as e:
                    log_operation("No Of Months", "WARN", f"Error selecting from dropdown: {e}")
            else:
                # Try as text input
                months_input = None
                months_input_selectors = [
                    (By.ID, "ctl00_ContentPlaceHolder1_txtNoOfMonths"),
                    (By.XPATH, "//input[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]"),
                    (By.XPATH, "//input[contains(@name, 'NoOfMonths') or contains(@name, 'Months')]"),
                    (By.XPATH, "//input[@type='text' and contains(@id, 'Months')]"),
                ]
                
                for by, selector in months_input_selectors:
                    try:
                        months_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                        log_operation("No Of Months", "SUCCESS", f"Found months input: {by}={selector}")
                        break
                    except:
                        continue
                
                if months_input:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", months_input)
                    time.sleep(0.5)
                    months_input.clear()
                    time.sleep(0.2)
                    months_input.send_keys("6")
                    time.sleep(0.3)
                    # Verify the value was set
                    input_value = months_input.get_attribute("value")
                    if input_value == "6":
                        log_operation("No Of Months", "SUCCESS", f"Filled No Of Months: 6 (verified: {input_value})")
                    else:
                        log_operation("No Of Months", "WARN", f"Value not set correctly. Expected '6', got '{input_value}'")
                else:
                    # Fallback to label-based method with multiple label variations
                    label_variations = ["No Of Months", "Months", "No. Of Months", "Number of Months", "Length of residence"]
                    for label_var in label_variations:
                        try:
                            fill_text_by_label(browser, wait, label_var, "6")
                            time.sleep(0.3)
                            # Try to verify
                            try:
                                verify_input = browser.find_element(By.XPATH, f"//input[contains(@id, 'Months')]")
                                verify_value = verify_input.get_attribute("value")
                                if verify_value == "6":
                                    log_operation("No Of Months", "SUCCESS", f"Filled using label variation: {label_var} (verified: {verify_value})")
                                    break
                                else:
                                    log_operation("No Of Months", "WARN", f"Filled using label but value not verified. Got: {verify_value}")
                            except:
                                log_operation("No Of Months", "SUCCESS", f"Filled using label variation: {label_var} (could not verify)")
                                break
                        except:
                            continue
            time.sleep(OPERATION_DELAY)
            
            # Check for page redirect after filling No Of Months
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("No Of Months", "WARN", "Page redirected to homepage after filling No Of Months, stopping...")
                return "homepage_redirect"
            
            # Check for error page
            error_result = check_and_handle_error_page(browser, wait)
            if error_result == "homepage_redirect":
                log_operation("No Of Months", "WARN", "Error page detected after filling No Of Months, redirected to homepage, stopping...")
                return "homepage_redirect"
            elif error_result == "application_error":
                log_operation("No Of Months", "ERROR", "Application error detected after filling No Of Months, stopping...")
                return "application_error"
            elif isinstance(error_result, str) and error_result.startswith("form_page_"):
                log_operation("No Of Months", "INFO", f"Page redirected to {error_result} after filling No Of Months, stopping...")
                return error_result
            
            # Check if URL changed (indicating page navigation)
            # Allow same form page URLs (e.g., VisaTypeDetails.aspx, ApplicantPersonalDetails.aspx, GeneralApplicantInfo.aspx)
            current_url_after = browser.current_url
            is_form_page_url = (
                "ApplicantPersonalDetails.aspx" in current_url_after or
                "VisaTypeDetails.aspx" in current_url_after or
                "GeneralApplicantInfo.aspx" in current_url_after or
                "StudentVisa.aspx" in current_url_after or
                "ApplicantFamilyDetails.aspx" in current_url_after or
                "ContactDetails.aspx" in current_url_after or
                "FormAssistance.aspx" in current_url_after
            )
            
            if not is_form_page_url:
                log_operation("No Of Months", "WARN", f"Page URL changed to non-form page after filling No Of Months: {current_url_after}, detecting page state...")
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
            elif current_url_after != initial_url and "GeneralApplicantInfo.aspx" in current_url_after:
                # URL changed to GeneralApplicantInfo.aspx (likely PostBack), verify field value was saved
                log_operation("No Of Months", "INFO", f"URL changed to GeneralApplicantInfo.aspx after selection, verifying field value was saved...")
                try:
                    time.sleep(1)  # Wait a bit for page to stabilize
                    months_dropdown_verify = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                    select_months_verify = Select(months_dropdown_verify)
                    selected_value_verify = select_months_verify.first_selected_option.text
                    if "6" in selected_value_verify:
                        log_operation("No Of Months", "SUCCESS", f"Field value verified after PostBack: {selected_value_verify}")
                    else:
                        log_operation("No Of Months", "WARN", f"Field value not saved after PostBack. Expected '6', got '{selected_value_verify}'")
                        # Try to select again
                        log_operation("No Of Months", "INFO", "Retrying selection after PostBack...")
                        select_months_verify.select_by_visible_text("6")
                        time.sleep(0.5)
                        selected_value_retry = select_months_verify.first_selected_option.text
                        if "6" in selected_value_retry:
                            log_operation("No Of Months", "SUCCESS", f"Field value saved after retry: {selected_value_retry}")
                        else:
                            log_operation("No Of Months", "WARN", f"Field value still not saved after retry: {selected_value_retry}")
                except Exception as e:
                    log_operation("No Of Months", "WARN", f"Could not verify field value after PostBack: {e}")
                # Don't return here - continue with the rest of the page filling
        except Exception as e:
            log_operation("No Of Months", "WARN", f"Error filling No Of Months: {e}")
            import traceback
            traceback.print_exc()
            
            # Check for page redirect even if there was an error
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                log_operation("No Of Months", "WARN", "Page redirected to homepage after error filling No Of Months, stopping...")
                return "homepage_redirect"
        
        # 3. Do you have permission to return to that country after your stay in Ireland?
        try:
            log_operation("Permission to return", "INFO", "Selecting permission to return...")
            select_radio_by_label(browser, wait, "Do you have permission to return to that country after your stay in Ireland", "Yes", alternative_values=["Y", "Yes", "1"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Permission to return", "WARN", f"Error selecting permission to return: {e}")
        
        # 4. Are you exempt from the requirement to provide biometrics?
        try:
            log_operation("Exempt from biometrics", "INFO", "Selecting exempt from biometrics...")
            select_radio_by_label(browser, wait, "Are you exempt from the requirement to provide biometrics", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Exempt from biometrics", "WARN", f"Error selecting exempt from biometrics: {e}")
        
        # 5. Have you applied for an Irish Visa/Preclearance before?
        try:
            log_operation("Applied before", "INFO", "Selecting applied before...")
            select_radio_by_label(browser, wait, "Have you applied for an Irish Visa/Preclearance before", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Applied before", "WARN", f"Error selecting applied before: {e}")
        
        # 6. Have you ever been issued with an Irish Visa/Preclearance before?
        try:
            log_operation("Issued before", "INFO", "Selecting issued before...")
            select_radio_by_label(browser, wait, "Have you ever been issued with an Irish Visa/Preclearance before", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Issued before", "WARN", f"Error selecting issued before: {e}")
        
        # 7. Please provide the location, application number and year of issue
        try:
            log_operation("Location, application number and year", "INFO", "Filling location, application number and year field...")
            fill_text_by_label(browser, wait, "Please provide the location, application number and year of issue", "N/A")
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Location, application number and year", "WARN", f"Error filling location, application number and year: {e}")
        
        # 8. Have you ever been refused an Irish Visa/Preclearance?
        try:
            log_operation("Refused Irish Visa", "INFO", "Selecting refused Irish Visa...")
            select_radio_by_label(browser, wait, "Have you ever been refused an Irish Visa/Preclearance", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Refused Irish Visa", "WARN", f"Error selecting refused Irish Visa: {e}")
        
        # 9. If you have been refused before, please provide location of application, year and reference number
        try:
            log_operation("Refused details", "INFO", "Filling refused details field...")
            fill_text_by_label(browser, wait, "If you have been refused before, please provide location of application, year and reference number", "N/A")
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Refused details", "WARN", f"Error filling refused details: {e}")
        
        # 10. Have you ever been in Ireland before?
        try:
            log_operation("Been in Ireland before", "INFO", "Selecting been in Ireland before...")
            select_radio_by_label(browser, wait, "Have you ever been in Ireland before", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Been in Ireland before", "WARN", f"Error selecting been in Ireland before: {e}")
        
        # 11. Do you have family members living in Ireland?
        try:
            log_operation("Family members in Ireland", "INFO", "Selecting family members in Ireland...")
            select_radio_by_label(browser, wait, "Do you have family members living in Ireland", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Family members in Ireland", "WARN", f"Error selecting family members in Ireland: {e}")
        
        # 12. Have you ever been refused permission to enter Ireland before?
        try:
            log_operation("Refused permission to enter", "INFO", "Selecting refused permission to enter...")
            select_radio_by_label(browser, wait, "Have you ever been refused permission to enter Ireland before", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Refused permission to enter", "WARN", f"Error selecting refused permission to enter: {e}")
        
        # 13. Have you ever been notified of a deportation order to leave Ireland?
        try:
            log_operation("Deportation order", "INFO", "Selecting deportation order...")
            select_radio_by_label(browser, wait, "Have you ever been notified of a deportation order to leave Ireland", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Deportation order", "WARN", f"Error selecting deportation order: {e}")
        
        # 14. Have you ever been refused a visa to another country?
        try:
            log_operation("Refused visa to another country", "INFO", "Selecting refused visa to another country...")
            select_radio_by_label(browser, wait, "Have you ever been refused a visa to another country", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Refused visa to another country", "WARN", f"Error selecting refused visa to another country: {e}")
        
        # 15. Have you ever been refused entry to, deported from, overstayed permission in, or were otherwise required to leave any country?
        try:
            log_operation("Refused entry or deported", "INFO", "Selecting refused entry or deported...")
            select_radio_by_label(browser, wait, "Have you ever been refused entry to, deported from, overstayed permission in, or were otherwise required to leave any country", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Refused entry or deported", "WARN", f"Error selecting refused entry or deported: {e}")
        
        # 16. If yes to any of the above please give details
        try:
            log_operation("Details if yes", "INFO", "Filling details if yes field...")
            fill_text_by_label(browser, wait, "If yes to any of the above please give details", "N/A")
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Details if yes", "WARN", f"Error filling details if yes: {e}")
        
        # 17. Have you any criminal convictions in any country?
        try:
            log_operation("Criminal convictions", "INFO", "Selecting criminal convictions...")
            select_radio_by_label(browser, wait, "Have you any criminal convictions in any country", "No", alternative_values=["N", "No", "0"])
            time.sleep(OPERATION_DELAY)
        except Exception as e:
            log_operation("Criminal convictions", "WARN", f"Error selecting criminal convictions: {e}")
        
        log_operation("fill_page_3", "SUCCESS", "Page 3 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_3", "INFO", f"Current URL after filling Page 3: {current_url}")
        
        # Check for homepage redirect after filling all fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Redirected to homepage after filling all fields, stopping...")
            return "homepage_redirect"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_page_3", "WARN", "Error page redirected to homepage, stopping...")
            return "homepage_redirect"
        
        # Check for homepage redirect after error page handling
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Redirected to homepage after error page handling, stopping...")
            return "homepage_redirect"
        
        # Verify page state before clicking button
        log_operation("fill_page_3", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_3", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_3", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_3", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Final check for homepage redirect before clicking button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_3", "WARN", "Redirected to homepage just before clicking button, stopping...")
            return "homepage_redirect"
        
        # Click Next/Continue button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_3_filled", output_dir=screenshots_dir)
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_3", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_3", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_3", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_3", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            
            # Check for validation errors BEFORE refreshing
            validation_errors = []
            try:
                # Check for various error indicators
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    validation_errors.extend([elem.text for elem in error_elements if elem.text])
                
                # Check for validation summary
                try:
                    validation_summary = browser.find_element(By.CLASS_NAME, "validation-summary")
                    if validation_summary:
                        validation_errors.append(validation_summary.text)
                except:
                    pass
                
                # Check for error messages in page source
                page_source = browser.page_source
                if "error" in page_source.lower() or "required" in page_source.lower() or "invalid" in page_source.lower():
                    # Try to find specific error messages
                    try:
                        error_spans = browser.find_elements(By.XPATH, "//span[contains(@class, 'error') or contains(@class, 'field-validation-error')]")
                        for span in error_spans:
                            if span.text and span.text.strip():
                                validation_errors.append(span.text)
                    except:
                        pass
                
                if validation_errors:
                    log_operation("fill_page_3", "ERROR", f"Found validation errors: {validation_errors}")
                    # Check which fields have errors
                    try:
                        # Check if "No Of Years" field has error
                        years_error = False
                        try:
                            years_input = browser.find_element(By.XPATH, "//input[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                            parent = years_input.find_element(By.XPATH, "./ancestor::td | ./ancestor::tr")
                            if "error" in parent.get_attribute("class") or "error" in parent.get_attribute("style"):
                                years_error = True
                                log_operation("fill_page_3", "ERROR", "No Of Years field has validation error")
                        except:
                            try:
                                years_select = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                                parent = years_select.find_element(By.XPATH, "./ancestor::td | ./ancestor::tr")
                                if "error" in parent.get_attribute("class") or "error" in parent.get_attribute("style"):
                                    years_error = True
                                    log_operation("fill_page_3", "ERROR", "No Of Years dropdown has validation error")
                            except:
                                pass
                        
                        # Check if "No Of Months" field has error
                        months_error = False
                        try:
                            months_input = browser.find_element(By.XPATH, "//input[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                            parent = months_input.find_element(By.XPATH, "./ancestor::td | ./ancestor::tr")
                            if "error" in parent.get_attribute("class") or "error" in parent.get_attribute("style"):
                                months_error = True
                                log_operation("fill_page_3", "ERROR", "No Of Months field has validation error")
                        except:
                            try:
                                months_select = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                                parent = months_select.find_element(By.XPATH, "./ancestor::td | ./ancestor::tr")
                                if "error" in parent.get_attribute("class") or "error" in parent.get_attribute("style"):
                                    months_error = True
                                    log_operation("fill_page_3", "ERROR", "No Of Months dropdown has validation error")
                            except:
                                pass
                        
                        if years_error or months_error:
                            log_operation("fill_page_3", "WARN", "Key fields have validation errors, returning form_page_3 to retry filling")
                            return "form_page_3"
                    except Exception as e:
                        log_operation("fill_page_3", "WARN", f"Error checking field validation: {e}")
            except Exception as e:
                log_operation("fill_page_3", "WARN", f"Error checking for validation errors: {e}")
            
            # Refresh page to get latest state
            log_operation("fill_page_3", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page after refresh
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_3", "WARN", f"Found validation errors after refresh: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_3", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_3", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Next button, check for Application Number
        # Application Number may appear after submitting page 3 or later
        time.sleep(2)  # Wait for page to load after navigation
        application_number = extract_application_number(browser, wait)
        if application_number:
            log_operation("fill_page_3", "SUCCESS", f"Application Number detected after Page 3: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        # Verify that we actually navigated away from page 3
        # If we're still on page 3, it means the form wasn't submitted successfully
        current_url_final = browser.current_url
        current_page_number = detect_page_number_no_refresh(browser, wait)
        
        if current_page_number == 3:
            log_operation("fill_page_3", "WARN", "Still on page 3 after clicking button - form may not have been submitted successfully")
            log_operation("fill_page_3", "INFO", f"Current URL: {current_url_final}")
            
            # Check for validation errors first
            validation_errors_found = False
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    if error_texts:
                        validation_errors_found = True
                        log_operation("fill_page_3", "ERROR", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Check if key fields are filled
            try:
                # Check if "No Of Years" field has a value
                years_filled = False
                years_value = None
                try:
                    years_input = browser.find_element(By.XPATH, "//input[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                    years_value = years_input.get_attribute("value")
                    if years_value and years_value.strip() and years_value != "":
                        years_filled = True
                        log_operation("fill_page_3", "INFO", f"No Of Years field has value: {years_value}")
                    else:
                        log_operation("fill_page_3", "WARN", f"No Of Years field is empty or has invalid value: '{years_value}'")
                except:
                    try:
                        years_select = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfYears') or contains(@id, 'Years')]")
                        select_obj = Select(years_select)
                        selected_value = select_obj.first_selected_option.text
                        years_value = selected_value
                        if selected_value and selected_value.strip() and selected_value != "" and selected_value.lower() != "--select--":
                            years_filled = True
                            log_operation("fill_page_3", "INFO", f"No Of Years dropdown has value: {selected_value}")
                        else:
                            log_operation("fill_page_3", "WARN", f"No Of Years dropdown is empty or has invalid value: '{selected_value}'")
                    except Exception as e:
                        log_operation("fill_page_3", "WARN", f"Could not find No Of Years field: {e}")
                
                # Check if "No Of Months" field has a value
                months_filled = False
                months_value = None
                try:
                    months_input = browser.find_element(By.XPATH, "//input[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                    months_value = months_input.get_attribute("value")
                    if months_value and months_value.strip() and months_value != "":
                        months_filled = True
                        log_operation("fill_page_3", "INFO", f"No Of Months field has value: {months_value}")
                    else:
                        log_operation("fill_page_3", "WARN", f"No Of Months field is empty or has invalid value: '{months_value}'")
                except:
                    try:
                        months_select = browser.find_element(By.XPATH, "//select[contains(@id, 'NoOfMonths') or contains(@id, 'Months')]")
                        select_obj = Select(months_select)
                        selected_value = select_obj.first_selected_option.text
                        months_value = selected_value
                        if selected_value and selected_value.strip() and selected_value != "" and selected_value.lower() != "--select--":
                            months_filled = True
                            log_operation("fill_page_3", "INFO", f"No Of Months dropdown has value: {selected_value}")
                        else:
                            log_operation("fill_page_3", "WARN", f"No Of Months dropdown is empty or has invalid value: '{selected_value}'")
                    except Exception as e:
                        log_operation("fill_page_3", "WARN", f"Could not find No Of Months field: {e}")
                
                # Log summary
                log_operation("fill_page_3", "INFO", f"Field status - Years: {years_filled} ({years_value}), Months: {months_filled} ({months_value}), Validation errors: {validation_errors_found}")
                
                if not years_filled or not months_filled:
                    log_operation("fill_page_3", "WARN", f"Required fields not filled - Years: {years_filled}, Months: {months_filled} - returning form_page_3 to retry")
                    return "form_page_3"
                
                if validation_errors_found:
                    log_operation("fill_page_3", "WARN", "Validation errors found - returning form_page_3 to retry")
                    return "form_page_3"
            except Exception as e:
                log_operation("fill_page_3", "WARN", f"Could not verify field values: {e}, returning form_page_3 to retry")
                import traceback
                traceback.print_exc()
                return "form_page_3"
        
        # Normal completion - only if we're not on page 3 anymore
        return "success"
        
    except Exception as e:
        log_operation("fill_page_3", "ERROR", f"Error filling Page 3: {e}")
        import traceback
        traceback.print_exc()
        return "error"




