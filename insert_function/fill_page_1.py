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

def fill_page_1(browser, wait, screenshots_dir=None):
    """
    Fill the first page of the application form
    
    Fields to fill:
    - Country Of Nationality: "People's Republic of China"
    - What is the reason for travel? *: "Study" (dropdown, not radio!)
    - What type of Visa/Preclearance are you applying for? *: "Long Stay (D)"
    - Journey Type: "Multiple"
    - Passport Type: "National Passport"
    - Passport/Travel Document Number: "112223"
    - Proposed dates: From "01/03/2026", To "08/03/2026"
    
    Returns:
        bool: True if page 1 was filled successfully, False if interrupted due to homepage redirect
    """
    log_operation("fill_page_1", "INFO", "Starting to fill Page 1...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_1", "WARN", "Already on homepage before starting Page 1, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        if not verify_page_state(browser, wait, 
                                expected_url_pattern="VisaTypeDetails.aspx",
                                operation_name="fill_page_1 (start)"):
            log_operation("fill_page_1", "WARN", "Page state verification failed at start, but continuing...")
        
        # Wait for page to load
        time.sleep(OPERATION_DELAY)
        
        # Check again after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_1", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # # Save page source to Markdown file
        # with open("page_source_debug.md", "w", encoding="utf-8") as f:
        #     f.write("```html\n")
        #     f.write(browser.page_source)
        #     f.write("\n```")

        # print("\n[INFO] Page source saved to 'page_source_debug.md'.\n")

        # Use direct ID-based approach for better reliability
        extended_wait = WebDriverWait(browser, 15)
        
        # 1. Country Of Nationality - using direct ID
        try:
            # Record current URL and page state before selection
            current_url = browser.current_url
            print(f"[INFO] Current URL before Country selection: {current_url}")
            
            country_select = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_select)
            time.sleep(0.5)
            
            # Check if dropdown has onchange event (indicates PostBack)
            has_postback = browser.execute_script("""
                var select = arguments[0];
                return select.onchange !== null || select.getAttribute('onchange') !== null;
            """, country_select)
            
            if has_postback:
                print("[INFO] Dropdown has PostBack behavior, will wait for page refresh...")
            
            select = Select(country_select)
            select.select_by_visible_text("People's Republic of China")
            print("[SUCCESS] Selected 'People's Republic of China' for Country Of Nationality")
            
            # Wait for PostBack to complete
            if has_postback:
                print("[INFO] Waiting for PostBack to complete...")
                try:
                    # Wait for page to start refreshing (element becomes stale)
                    time.sleep(1)
                    
                    # Wait for page to reload - check if element becomes stale or page changes
                    # Use a custom wait that checks for homepage redirect
                    max_wait_time = 30
                    start_time = time.time()
                    page_ready = False
                    
                    while time.time() - start_time < max_wait_time:
                        try:
                            ready_state = browser.execute_script("return document.readyState")
                            current_url_check = browser.current_url
                            
                            # Check if redirected to homepage
                            if "OnlineHome.aspx" in current_url_check:
                                log_operation("Country Of Nationality", "WARN", "Detected redirect to homepage during PostBack wait - stopping immediately")
                                return "homepage_redirect"
                            
                            if ready_state == "complete":
                                page_ready = True
                                break
                            
                            time.sleep(0.5)
                        except:
                            time.sleep(0.5)
                    
                    if not page_ready:
                        log_operation("Country Of Nationality", "WARN", "Page ready state timeout, but continuing...")
                    
                    # Check URL again after page is ready
                    new_url = browser.current_url
                    print(f"[INFO] URL after PostBack: {new_url}")
                    
                    # Check for error page first
                    if "ApplicationError.aspx" in new_url or "Error" in new_url:
                        log_operation("Country Of Nationality", "ERROR", f"Detected error page after PostBack: {new_url}")
                        # Try to handle the error page
                        check_and_handle_error_page(browser, wait)
                        # Wait a bit to see if error page redirects
                        time.sleep(3)
                        error_url_after = browser.current_url
                        log_operation("Country Of Nationality", "INFO", f"URL after error page handling: {error_url_after}")
                        
                        # If still on error page or redirected to homepage, return homepage_redirect
                        if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after:
                            log_operation("Country Of Nationality", "WARN", "Still on error page after handling - returning homepage_redirect")
                            return "homepage_redirect"
                        elif "OnlineHome.aspx" in error_url_after:
                            log_operation("Country Of Nationality", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                            return "homepage_redirect"
                        elif "VisaTypeDetails.aspx" in error_url_after:
                            log_operation("Country Of Nationality", "INFO", "Error page redirected back to form page - continuing")
                            # Continue with element wait
                        else:
                            log_operation("Country Of Nationality", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                            return "homepage_redirect"
                    
                    if "OnlineHome.aspx" in new_url:
                        log_operation("Country Of Nationality", "WARN", "Page redirected to homepage after PostBack - stopping immediately")
                        return "homepage_redirect"
                    
                    # Wait for the same element to be present again (page reloaded)
                    # Use a custom wait that checks for homepage redirect
                    element_found = False
                    max_element_wait = 20
                    element_start_time = time.time()
                    
                    while time.time() - element_start_time < max_element_wait:
                        try:
                            # Check for error page or homepage redirect first
                            current_url_check = browser.current_url
                            if "ApplicationError.aspx" in current_url_check or "Error" in current_url_check:
                                log_operation("Country Of Nationality", "ERROR", f"Detected error page while waiting for element: {current_url_check}")
                                # Try to handle the error page
                                check_and_handle_error_page(browser, wait)
                                time.sleep(2)
                                error_url_after = browser.current_url
                                if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after or "OnlineHome.aspx" in error_url_after:
                                    log_operation("Country Of Nationality", "WARN", "Error page detected or redirected to homepage - returning homepage_redirect")
                                    return "homepage_redirect"
                                # If redirected back to form page, continue
                            elif "OnlineHome.aspx" in current_url_check:
                                log_operation("Country Of Nationality", "WARN", "Detected redirect to homepage while waiting for element - stopping immediately")
                                return "homepage_redirect"
                            
                            # Try to find the element
                            country_select_check = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                            if country_select_check:
                                element_found = True
                                break
                        except:
                            pass
                        
                        time.sleep(0.5)
                    
                    if not element_found:
                        # Check URL one more time
                        final_url_check = browser.current_url
                        if "ApplicationError.aspx" in final_url_check or "Error" in final_url_check:
                            log_operation("Country Of Nationality", "ERROR", f"Element not found and page is on error page: {final_url_check}")
                            check_and_handle_error_page(browser, wait)
                            time.sleep(2)
                            error_final_url = browser.current_url
                            if "ApplicationError.aspx" in error_final_url or "Error" in error_final_url or "OnlineHome.aspx" in error_final_url:
                                log_operation("Country Of Nationality", "WARN", "Error page detected or redirected to homepage - returning homepage_redirect")
                                return "homepage_redirect"
                        elif "OnlineHome.aspx" in final_url_check:
                            log_operation("Country Of Nationality", "WARN", "Element not found and page is on homepage - stopping immediately")
                            return "homepage_redirect"
                        else:
                            log_operation("Country Of Nationality", "WARN", "Element not found after PostBack, but continuing...")
                    
                    # Verify we're still on the form page (not redirected to homepage)
                    new_url = browser.current_url
                    print(f"[INFO] URL after PostBack: {new_url}")
                    
                    if "OnlineHome.aspx" in new_url:
                        log_operation("Country Of Nationality", "WARN", "Page redirected to homepage after PostBack - stopping immediately")
                        return "homepage_redirect"
                    
                    # Additional wait for dynamic content
                    time.sleep(POSTBACK_WAIT_DELAY)
                    log_operation("Country Of Nationality", "SUCCESS", "PostBack completed, page reloaded successfully")
                    
                    # Check for error page after PostBack
                    check_and_handle_error_page(browser, wait)
                    
                    # Verify page state after PostBack
                    if not verify_page_state(browser, wait, 
                                            expected_url_pattern="VisaTypeDetails.aspx",
                                            required_elements=[(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")],
                                            operation_name="Country Of Nationality (after PostBack)"):
                        log_operation("Country Of Nationality", "WARN", "Page state verification failed after PostBack")
                    
                    # Delay between PostBack operations
                    time.sleep(POSTBACK_BETWEEN_DELAY)
                except TimeoutException:
                    print("[WARN] Initial PostBack wait timeout for Country Of Nationality, continuing to wait until PostBack completes...")
                    # Wait indefinitely until PostBack completes or page redirects
                    postback_completed = False
                    check_count = 0
                    homepage_detected_count = 0  # Count how many times we detect homepage
                    
                    while not postback_completed:
                        try:
                            check_count += 1
                            if check_count % 10 == 0:  # Print status every 10 seconds
                                print(f"[INFO] Still waiting for PostBack to complete... (checked {check_count} times)")
                            
                            # Check for error page first (before checking other states)
                            error_result = check_and_handle_error_page(browser, wait)
                            if error_result == "homepage_redirect":
                                log_operation("Country Of Nationality", "WARN", "Error page redirected to homepage during PostBack wait - returning homepage_redirect")
                                return "homepage_redirect"
                            elif error_result == True:
                                log_operation("Country Of Nationality", "WARN", "Error page detected during PostBack wait - checking URL after handling...")
                                # Wait a bit to see if error page handling resolved the issue
                                time.sleep(3)
                                error_url_after = browser.current_url
                                if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after:
                                    log_operation("Country Of Nationality", "WARN", "Still on error page after handling - returning homepage_redirect")
                                    return "homepage_redirect"
                                elif "OnlineHome.aspx" in error_url_after:
                                    log_operation("Country Of Nationality", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                    return "homepage_redirect"
                                elif "VisaTypeDetails.aspx" in error_url_after:
                                    log_operation("Country Of Nationality", "INFO", "Error page redirected back to form page - continuing")
                                    # Continue with normal PostBack wait
                                else:
                                    log_operation("Country Of Nationality", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                    return "homepage_redirect"
                            
                            # Check document ready state
                            ready_state = browser.execute_script("return document.readyState")
                            current_url_check = browser.current_url
                            
                            # Check for error page URL
                            if "ApplicationError.aspx" in current_url_check or "Error.aspx" in current_url_check:
                                log_operation("Country Of Nationality", "ERROR", f"Detected error page URL during PostBack wait: {current_url_check}")
                                error_result = check_and_handle_error_page(browser, wait)
                                if error_result == "homepage_redirect":
                                    log_operation("Country Of Nationality", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                    return "homepage_redirect"
                                elif error_result == True:
                                    time.sleep(3)
                                    error_url_after = browser.current_url
                                    if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after or "OnlineHome.aspx" in error_url_after:
                                        log_operation("Country Of Nationality", "WARN", "Error page detected or redirected to homepage - returning homepage_redirect")
                                        return "homepage_redirect"
                                    elif "VisaTypeDetails.aspx" in error_url_after:
                                        log_operation("Country Of Nationality", "INFO", "Error page redirected back to form page - continuing")
                                        # Continue with normal PostBack wait
                                    else:
                                        log_operation("Country Of Nationality", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                        return "homepage_redirect"
                            
                            # If redirected to homepage, wait a bit to see if it redirects back
                            if "OnlineHome.aspx" in current_url_check:
                                homepage_detected_count += 1
                                if homepage_detected_count == 1:
                                    print("[WARN] Detected redirect to homepage during PostBack wait")
                                    print("[INFO] Waiting 5 seconds to see if page automatically redirects back to form...")
                                    time.sleep(5)
                                    
                                    # Check again
                                    check_url_after_wait = browser.current_url
                                    if "VisaTypeDetails.aspx" in check_url_after_wait:
                                        print("[SUCCESS] Page automatically redirected back to form page")
                                        # Wait for element to be present
                                        try:
                                            extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")))
                                            ready_state_after = browser.execute_script("return document.readyState")
                                            if ready_state_after == "complete":
                                                print("[SUCCESS] PostBack completed after redirect back to form")
                                                postback_completed = True
                                                time.sleep(2)
                                                break
                                        except:
                                            pass
                                    elif "OnlineHome.aspx" in check_url_after_wait:
                                        log_operation("Country Of Nationality", "WARN", "Still on homepage after waiting - returning homepage_redirect")
                                        return "homepage_redirect"
                                elif homepage_detected_count > 3:
                                    # If we've detected homepage multiple times, it's likely a permanent redirect
                                    log_operation("Country Of Nationality", "ERROR", "Page repeatedly redirected to homepage - returning homepage_redirect")
                                    return "homepage_redirect"
                            
                            # Check if we're still on form page
                            if "VisaTypeDetails.aspx" in current_url_check:
                                # Check if key element is present
                                try:
                                    country_select_found = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")
                                    if ready_state == "complete" and country_select_found:
                                        print("[SUCCESS] PostBack completed after extended wait")
                                        postback_completed = True
                                        time.sleep(2)  # Additional wait for dynamic content
                                        break
                                except:
                                    pass
                            
                            time.sleep(1)  # Check every second
                        except Exception as e:
                            print(f"[DEBUG] Error checking page state: {e}")
                            time.sleep(1)
            else:
                time.sleep(1)  # Short wait if no PostBack
                
        except Exception as e:
            print(f"[WARN] Could not fill Country Of Nationality by ID: {e}")
            fill_dropdown_by_label(browser, wait, "Country Of Nationality", "People's Republic of China")
        
        # 2. What is the reason for travel? - This is a DROPDOWN, not radio!
        try:
            # Record current URL before selection
            current_url = browser.current_url
            print(f"[INFO] Current URL before reason selection: {current_url}")
            
            reason_select = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlVisaCategory")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reason_select)
            time.sleep(0.5)
            
            # Check if dropdown has PostBack
            has_postback = browser.execute_script("""
                var select = arguments[0];
                return select.onchange !== null || select.getAttribute('onchange') !== null;
            """, reason_select)
            
            if has_postback:
                print("[INFO] Reason dropdown has PostBack behavior, will wait for page refresh...")
            
            select = Select(reason_select)
            # Try to select "Study"
            select.select_by_visible_text("Study")
            print("[SUCCESS] Selected 'Study' for reason for travel")
            
            # Wait for PostBack to complete
            if has_postback:
                print("[INFO] Waiting for PostBack to complete...")
                try:
                    time.sleep(1)
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlVisaCategory")))
                    
                    new_url = browser.current_url
                    print(f"[INFO] URL after PostBack: {new_url}")
                    
                    if "VisaTypeDetails.aspx" not in new_url and "OnlineHome.aspx" in new_url:
                        log_operation("Reason for travel", "WARN", "Page redirected to homepage after PostBack - returning homepage_redirect")
                        return "homepage_redirect"
                    
                    time.sleep(POSTBACK_WAIT_DELAY)
                    log_operation("Reason for travel", "SUCCESS", "PostBack completed")
                    
                    # Check for error page after PostBack
                    check_and_handle_error_page(browser, wait)
                    
                    # Verify page state after PostBack
                    if not verify_page_state(browser, wait, 
                                            expected_url_pattern="VisaTypeDetails.aspx",
                                            operation_name="Reason for travel (after PostBack)"):
                        log_operation("Reason for travel", "WARN", "Page state verification failed after PostBack")
                    
                    # Delay between PostBack operations
                    time.sleep(POSTBACK_BETWEEN_DELAY)
                    
                    # After selecting "Study", check if Study Type dropdown appears
                    # This field is dynamically shown after PostBack
                    # Note: We fill Study Type BEFORE other fields (Visa Type, Journey Type) 
                    # because it appears immediately after selecting "Study" and may be required
                    try:
                        print("[INFO] Checking for Study Type field after PostBack...")
                        # Additional wait to ensure Study Type field is fully rendered
                        time.sleep(1)
                        study_type_selectors = [
                            (By.ID, "ctl00_ContentPlaceHolder1_studyTypeDropDownList"),
                            (By.ID, "ctl00_ContentPlaceHolder1_ddlStudyType"),
                            (By.XPATH, "//select[contains(@id, 'StudyType') or contains(@id, 'studyType')]"),
                            (By.XPATH, "//*[contains(text(), 'type of Study') or contains(text(), 'Study Type')]//following::select[1]"),
                            (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyType']//select"),
                        ]
                        
                        study_type_select = None
                        for selector_type, selector_value in study_type_selectors:
                            try:
                                study_type_select = extended_wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                                print(f"[SUCCESS] Found Study Type dropdown using: {selector_type}")
                                break
                            except TimeoutException:
                                continue
                        
                        if study_type_select:
                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", study_type_select)
                            time.sleep(0.5)
                            
                            # Check if dropdown has PostBack behavior
                            study_type_id = study_type_select.get_attribute("id")
                            has_postback = browser.execute_script("""
                                var select = arguments[0];
                                return select.onchange !== null || select.getAttribute('onchange') !== null;
                            """, study_type_select)
                            
                            if has_postback:
                                print("[INFO] Study Type dropdown has PostBack behavior, will wait for page refresh...")
                            
                            # Record current URL if PostBack is expected
                            current_url = None
                            if has_postback:
                                current_url = browser.current_url
                                print(f"[INFO] Current URL before Study Type selection: {current_url}")
                            
                            # Try to select "English Language (ILEP)" first (default choice)
                            select = Select(study_type_select)
                            
                            # Priority: English Language (ILEP) as default
                            study_type_options = [
                                "English Language (ILEP)",  # Default first choice
                                "Foundation/Preparatory Courses (ILEP)",
                                "Higher Education/Professional (ILEP)",
                                "English Language",
                                "Foundation",
                                "Higher Education"
                            ]
                            
                            selected_study_type = False
                            for option_text in study_type_options:
                                try:
                                    select.select_by_visible_text(option_text)
                                    print(f"[SUCCESS] Selected '{option_text}' for Study Type")
                                    selected_study_type = True
                                    
                                    # Wait for PostBack if it was triggered
                                    if has_postback:
                                        log_operation("Study Type", "INFO", "Waiting for PostBack to complete after Study Type selection...")
                                        
                                        # Add delay before PostBack
                                        time.sleep(POSTBACK_DELAY)
                                        
                                        try:
                                            # Wait for page to start refreshing
                                            time.sleep(1)
                                            
                                            # Wait for document ready state with longer timeout
                                            extended_wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                            
                                            # Wait for the select element to be present again (page reloaded)
                                            if study_type_id:
                                                try:
                                                    extended_wait.until(EC.presence_of_element_located((By.ID, study_type_id)))
                                                except:
                                                    # If element not found by ID, try to find it again
                                                    extended_wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'StudyType') or contains(@id, 'studyType')]")))
                                            
                                            # Verify we're still on the form page
                                            new_url = browser.current_url
                                            print(f"[INFO] URL after Study Type PostBack: {new_url}")
                                            
                                            if current_url and "VisaTypeDetails.aspx" not in new_url and "OnlineHome.aspx" in new_url:
                                                log_operation("Study Type", "WARN", "Page redirected to homepage after Study Type PostBack - returning homepage_redirect")
                                                # Return homepage_redirect to indicate that page 1 was interrupted
                                                return "homepage_redirect"
                                            
                                            # Additional wait for dynamic content
                                            time.sleep(POSTBACK_WAIT_DELAY)
                                            log_operation("Study Type", "SUCCESS", "PostBack completed")
                                            
                                            # Check for error page after PostBack
                                            check_and_handle_error_page(browser, wait)
                                            
                                            # Verify page state after PostBack
                                            if not verify_page_state(browser, wait, 
                                                                    expected_url_pattern="VisaTypeDetails.aspx",
                                                                    operation_name="Study Type (after PostBack)"):
                                                log_operation("Study Type", "WARN", "Page state verification failed after PostBack")
                                            
                                            # Delay between PostBack operations
                                            time.sleep(POSTBACK_BETWEEN_DELAY)
                                            
                                            # After Study Type PostBack, fill ILEP number field if it appears
                                            # This field typically appears after selecting "English Language (ILEP)"
                                            # Based on debug files, ILEP field is a direct text input, not a checkbox
                                            try:
                                                print("[INFO] Checking for ILEP number field after Study Type PostBack...")
                                                time.sleep(2)  # Wait for ILEP field to appear after PostBack
                                                
                                                # According to debug files, ILEP field is a direct text input
                                                # Try to find ILEP text input directly first
                                                print("[INFO] Looking for ILEP text input field directly (no checkbox)...")
                                                ilep_input = None
                                                ilep_input_selectors = [
                                                    # Direct text input selectors (priority)
                                                    (By.XPATH, "//input[@type='text' and contains(@id, 'ILEP')]"),
                                                    (By.XPATH, "//input[@type='text' and contains(@name, 'ILEP')]"),
                                                    (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyEnglishILEP']//input[@type='text']"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_txtILEP"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_txtILEPNumber"),
                                                    (By.XPATH, "//input[contains(@id, 'ILEP') and @type='text']"),
                                                    (By.XPATH, "//input[contains(@name, 'ILEP') and @type='text']"),
                                                ]
                                                
                                                for by, selector in ilep_input_selectors:
                                                    try:
                                                        quick_wait = WebDriverWait(browser, 3)
                                                        ilep_input = quick_wait.until(EC.presence_of_element_located((by, selector)))
                                                        print(f"[SUCCESS] Found ILEP text input using: {by}={selector}")
                                                        break
                                                    except (TimeoutException, NoSuchElementException):
                                                        print(f"[DEBUG] ILEP text input not found with: {by}={selector}, trying next selector...")
                                                        continue
                                                
                                                # If direct input not found, check if there's a checkbox pattern (fallback)
                                                # Note: According to debug files, ILEP field is typically a direct text input
                                                ilep_checkbox = None
                                                if not ilep_input:
                                                    print("[INFO] Direct ILEP text input not found, checking for checkbox pattern (fallback)...")
                                                    ilep_field_selectors = [
                                                        # Checkbox + input field pattern (fallback)
                                                        (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyEnglishILEP']//input[@type='checkbox']"),
                                                        (By.XPATH, "//*[contains(text(), 'I know my ILEP number') or contains(text(), 'ILEP number')]//preceding::input[@type='checkbox'][1]"),
                                                        (By.XPATH, "//*[contains(text(), 'I know my ILEP number') or contains(text(), 'ILEP number')]//following::input[@type='checkbox'][1]"),
                                                        (By.XPATH, "//label[contains(text(), 'I know my ILEP number')]//preceding::input[@type='checkbox'][1]"),
                                                        (By.XPATH, "//label[contains(text(), 'I know my ILEP number')]//following::input[@type='checkbox'][1]"),
                                                        # Direct ID patterns
                                                        (By.ID, "ctl00_ContentPlaceHolder1_chkILEP"),
                                                        (By.ID, "ctl00_ContentPlaceHolder1_chkKnowILEP"),
                                                        (By.XPATH, "//input[contains(@id, 'ILEP') and @type='checkbox']"),
                                                    ]
                                                    
                                                    for by, selector in ilep_field_selectors:
                                                        try:
                                                            quick_wait = WebDriverWait(browser, 3)
                                                            ilep_checkbox = quick_wait.until(EC.presence_of_element_located((by, selector)))
                                                            print(f"[SUCCESS] Found ILEP checkbox using: {by}={selector}")
                                                            break
                                                        except (TimeoutException, NoSuchElementException):
                                                            print(f"[DEBUG] ILEP checkbox not found with: {by}={selector}, trying next selector...")
                                                            continue
                                                
                                                # Process ILEP field: if we found direct input, use it; otherwise use checkbox pattern
                                                if ilep_input:
                                                    # ILEP field is a direct text input (most common case)
                                                    # Fill the input field directly
                                                    try:
                                                        log_operation("ILEP Number", "INFO", "Filling ILEP number field directly...")
                                                        
                                                        # Scroll to input field using safe method
                                                        try:
                                                            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_input)
                                                        except Exception as scroll_error:
                                                            # If scrollIntoView fails, try alternative method
                                                            print(f"[DEBUG] scrollIntoView failed, trying alternative: {scroll_error}")
                                                            try:
                                                                browser.execute_script("arguments[0].scrollIntoView(true);", ilep_input)
                                                            except:
                                                                # Last resort: use ActionChains
                                                                ActionChains(browser).move_to_element(ilep_input).perform()
                                                        time.sleep(0.5)
                                                        
                                                        # Delay before filling
                                                        time.sleep(OPERATION_DELAY)
                                                        
                                                        # Clear existing value and fill
                                                        ilep_input.clear()
                                                        time.sleep(0.2)
                                                        
                                                        # Type the ILEP number
                                                        ilep_input.send_keys("0365/0002")
                                                        log_operation("ILEP Number", "INFO", "Typed ILEP number: 0365/0002")
                                                        
                                                        # Wait for autocomplete/dropdown options to appear
                                                        time.sleep(1)  # Wait for dropdown to appear
                                                        log_operation("ILEP Number", "INFO", "Waiting for autocomplete options to appear...")
                                                        
                                                        # Try to find and select the autocomplete option
                                                        autocomplete_selected = False
                                                        autocomplete_selectors = [
                                                            # Common autocomplete/dropdown patterns
                                                            (By.XPATH, "//ul[@class='ui-autocomplete' or contains(@class, 'autocomplete')]//li[contains(text(), '0365/0002')]"),
                                                            (By.XPATH, "//div[@class='autocomplete' or contains(@class, 'dropdown')]//div[contains(text(), '0365/0002')]"),
                                                            (By.XPATH, "//li[contains(text(), '0365/0002') or contains(text(), '0365')]"),
                                                            (By.XPATH, "//div[contains(@class, 'suggestion') or contains(@class, 'option')][contains(text(), '0365/0002')]"),
                                                            (By.XPATH, "//*[@role='option' or @role='listbox']//*[contains(text(), '0365/0002')]"),
                                                            # Try to find first option in dropdown
                                                            (By.XPATH, "//ul[contains(@class, 'ui-autocomplete')]//li[1]"),
                                                            (By.XPATH, "//div[contains(@class, 'autocomplete')]//div[1]"),
                                                        ]
                                                        
                                                        for by, selector in autocomplete_selectors:
                                                            try:
                                                                quick_wait = WebDriverWait(browser, 2)
                                                                autocomplete_option = quick_wait.until(EC.element_to_be_clickable((by, selector)))
                                                                if autocomplete_option.is_displayed():
                                                                    log_operation("ILEP Number", "SUCCESS", f"Found autocomplete option: {by}={selector}")
                                                                    # Scroll to option
                                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", autocomplete_option)
                                                                    time.sleep(0.3)
                                                                    # Click the option
                                                                    autocomplete_option.click()
                                                                    log_operation("ILEP Number", "SUCCESS", "Selected autocomplete option")
                                                                    autocomplete_selected = True
                                                                    time.sleep(0.5)
                                                                    break
                                                            except (TimeoutException, NoSuchElementException):
                                                                continue
                                                        
                                                        # If no option found by clicking, try keyboard navigation
                                                        if not autocomplete_selected:
                                                            log_operation("ILEP Number", "INFO", "Autocomplete option not found by clicking, trying keyboard navigation...")
                                                            try:
                                                                # Press Arrow Down to select first option, then Enter
                                                                ilep_input.send_keys(Keys.ARROW_DOWN)
                                                                time.sleep(0.3)
                                                                ilep_input.send_keys(Keys.ENTER)
                                                                log_operation("ILEP Number", "SUCCESS", "Selected autocomplete option using keyboard (Arrow Down + Enter)")
                                                                autocomplete_selected = True
                                                                time.sleep(0.5)
                                                            except Exception as kb_error:
                                                                log_operation("ILEP Number", "WARN", f"Keyboard navigation failed: {kb_error}, continuing without selecting option...")
                                                        
                                                        if autocomplete_selected:
                                                            log_operation("ILEP Number", "SUCCESS", "ILEP number autocomplete option selected")
                                                        else:
                                                            log_operation("ILEP Number", "WARN", "Could not select autocomplete option, but continuing...")
                                                        
                                                        # Additional wait after selecting option
                                                        time.sleep(0.5)
                                                        
                                                        # Check if input field has PostBack behavior (onchange event)
                                                        try:
                                                            has_ilep_postback = browser.execute_script("""
                                                                var input = arguments[0];
                                                                return input.onchange !== null || input.getAttribute('onchange') !== null;
                                                            """, ilep_input)
                                                        except Exception as e_check:
                                                            print(f"[DEBUG] Error checking PostBack: {e_check}")
                                                            has_ilep_postback = False
                                                        
                                                        if has_ilep_postback:
                                                            log_operation("ILEP Number", "INFO", "ILEP number input has PostBack behavior, waiting for page refresh...")
                                                            # Record current URL before PostBack
                                                            current_url_before = browser.current_url
                                                            log_operation("ILEP Number", "INFO", f"Current URL before ILEP PostBack: {current_url_before}")
                                                            
                                                            # Get the input ID before PostBack (element will become stale)
                                                            ilep_input_id = ilep_input.get_attribute("id") or ""
                                                            ilep_input_name = ilep_input.get_attribute("name") or ""
                                                            
                                                            # Trigger change event to initiate PostBack
                                                            try:
                                                                browser.execute_script("arguments[0].dispatchEvent(new Event('change'));", ilep_input)
                                                            except Exception as e_trigger:
                                                                print(f"[DEBUG] Error triggering change event: {e_trigger}")
                                                                # Try alternative: directly set value and trigger
                                                                try:
                                                                    browser.execute_script("""
                                                                        var input = document.getElementById(arguments[0]) || document.querySelector('[name="' + arguments[1] + '"]');
                                                                        if (input) {
                                                                            input.value = arguments[2];
                                                                            input.dispatchEvent(new Event('change'));
                                                                        }
                                                                    """, ilep_input_id, ilep_input_name, "0365/0002")
                                                                except:
                                                                    pass
                                                            time.sleep(0.5)
                                                            
                                                            # Wait for PostBack to complete
                                                            log_operation("ILEP Number", "INFO", "Waiting for PostBack to complete after ILEP number input...")
                                                            try:
                                                                # Wait for page to start refreshing
                                                                time.sleep(1)
                                                                
                                                                # Wait for document ready state
                                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                
                                                                # Wait for the input field to reappear (page reloaded)
                                                                # Use the ID or name we saved before PostBack
                                                                if ilep_input_id:
                                                                    extended_wait.until(EC.presence_of_element_located((By.ID, ilep_input_id)))
                                                                else:
                                                                    extended_wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'ILEP') and @type='text']")))
                                                                
                                                                # Verify we're still on the form page
                                                                new_url_after = browser.current_url
                                                                log_operation("ILEP Number", "INFO", f"URL after ILEP PostBack: {new_url_after}")
                                                                
                                                                if "VisaTypeDetails.aspx" not in new_url_after and "OnlineHome.aspx" in new_url_after:
                                                                    log_operation("ILEP Number", "WARN", "Page redirected to homepage after ILEP PostBack - returning homepage_redirect")
                                                                    return "homepage_redirect"
                                                                
                                                                # Additional wait for dynamic content
                                                                time.sleep(POSTBACK_WAIT_DELAY)
                                                                log_operation("ILEP Number", "SUCCESS", "PostBack completed")
                                                                
                                                                # Check for error page after PostBack
                                                                check_and_handle_error_page(browser, wait)
                                                                
                                                                # Verify page state after PostBack
                                                                if not verify_page_state(browser, wait, 
                                                                                        expected_url_pattern="VisaTypeDetails.aspx",
                                                                                        operation_name="ILEP Number (after PostBack)"):
                                                                    log_operation("ILEP Number", "WARN", "Page state verification failed after PostBack")
                                                                
                                                                # Delay after PostBack operation
                                                                time.sleep(POSTBACK_BETWEEN_DELAY)
                                                            except TimeoutException:
                                                                log_operation("ILEP Number", "WARN", "Initial ILEP PostBack wait timeout, continuing to wait until PostBack completes...")
                                                                # Wait indefinitely until PostBack completes or page redirects
                                                                postback_completed = False
                                                                check_count = 0
                                                                
                                                                while not postback_completed:
                                                                    try:
                                                                        check_count += 1
                                                                        if check_count % 10 == 0:  # Print status every 10 seconds
                                                                            print(f"[INFO] Still waiting for ILEP PostBack to complete... (checked {check_count} times)")
                                                                        
                                                                        # Check for error page first (before checking other states)
                                                                        error_result = check_and_handle_error_page(browser, wait)
                                                                        if error_result == "homepage_redirect":
                                                                            log_operation("ILEP Number", "WARN", "Error page redirected to homepage during PostBack wait - returning homepage_redirect")
                                                                            return "homepage_redirect"
                                                                        elif error_result == True:
                                                                            log_operation("ILEP Number", "WARN", "Error page detected during PostBack wait - checking URL after handling...")
                                                                            # Wait a bit to see if error page handling resolved the issue
                                                                            time.sleep(3)
                                                                            error_url_after = browser.current_url
                                                                            if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after:
                                                                                log_operation("ILEP Number", "WARN", "Still on error page after handling - returning homepage_redirect")
                                                                                return "homepage_redirect"
                                                                            elif "OnlineHome.aspx" in error_url_after:
                                                                                log_operation("ILEP Number", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                                                                return "homepage_redirect"
                                                                            elif "VisaTypeDetails.aspx" in error_url_after:
                                                                                log_operation("ILEP Number", "INFO", "Error page redirected back to form page - continuing")
                                                                                # Continue with normal PostBack wait
                                                                            else:
                                                                                log_operation("ILEP Number", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                                                                return "homepage_redirect"
                                                                        
                                                                        # Check document ready state
                                                                        ready_state = browser.execute_script("return document.readyState")
                                                                        current_url_check = browser.current_url
                                                                        
                                                                        # Check for error page URL
                                                                        if "ApplicationError.aspx" in current_url_check or "Error.aspx" in current_url_check:
                                                                            log_operation("ILEP Number", "ERROR", f"Detected error page URL during PostBack wait: {current_url_check}")
                                                                            error_result = check_and_handle_error_page(browser, wait)
                                                                            if error_result == "homepage_redirect":
                                                                                log_operation("ILEP Number", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                                                                return "homepage_redirect"
                                                                            elif error_result == True:
                                                                                time.sleep(3)
                                                                                error_url_after = browser.current_url
                                                                                if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after or "OnlineHome.aspx" in error_url_after:
                                                                                    log_operation("ILEP Number", "WARN", "Error page detected or redirected to homepage - returning homepage_redirect")
                                                                                    return "homepage_redirect"
                                                                                elif "VisaTypeDetails.aspx" in error_url_after:
                                                                                    log_operation("ILEP Number", "INFO", "Error page redirected back to form page - continuing")
                                                                                    # Continue with normal PostBack wait
                                                                                else:
                                                                                    log_operation("ILEP Number", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                                                                    return "homepage_redirect"
                                                                        
                                                                        # If redirected to homepage, return homepage_redirect
                                                                        if "OnlineHome.aspx" in current_url_check:
                                                                            log_operation("ILEP Number", "WARN", "Page redirected to homepage during ILEP PostBack wait - returning homepage_redirect")
                                                                            return "homepage_redirect"
                                                                        
                                                                        # Check if we're still on form page
                                                                        if "VisaTypeDetails.aspx" in current_url_check:
                                                                            # Check if ILEP field is present
                                                                            try:
                                                                                ilep_field_found = browser.find_elements(By.XPATH, "//input[contains(@id, 'ILEP')]")
                                                                                if ready_state == "complete" and ilep_field_found:
                                                                                    log_operation("ILEP Number", "SUCCESS", "ILEP PostBack completed after extended wait")
                                                                                    postback_completed = True
                                                                                    time.sleep(2)  # Additional wait for dynamic content
                                                                                    break
                                                                            except:
                                                                                pass
                                                                        
                                                                        time.sleep(1)  # Check every second
                                                                    except Exception as e:
                                                                        print(f"[DEBUG] Error checking page state: {e}")
                                                                        time.sleep(1)
                                                        else:
                                                            # No PostBack, just a short wait
                                                            time.sleep(0.5)
                                                    except Exception as e_fill:
                                                        log_operation("ILEP Number", "WARN", f"Error filling ILEP input field: {e_fill}")
                                                        # Clear reference to avoid using stale element
                                                        ilep_input = None
                                                        import traceback
                                                        traceback.print_exc()
                                                elif ilep_checkbox:
                                                    # Scroll to checkbox
                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_checkbox)
                                                    time.sleep(0.5)
                                                    
                                                    # Check if checkbox is already checked
                                                    if not ilep_checkbox.is_selected():
                                                        ilep_checkbox.click()
                                                        print("[SUCCESS] Checked 'I know my ILEP number' checkbox")
                                                        time.sleep(0.5)
                                                    
                                                    # Now find the ILEP number input field
                                                    ilep_input_selectors = [
                                                        (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyEnglishILEP']//input[@type='text']"),
                                                        (By.XPATH, "//*[contains(text(), 'I know my ILEP number') or contains(text(), 'ILEP number')]//following::input[@type='text'][1]"),
                                                        (By.XPATH, "//label[contains(text(), 'I know my ILEP number')]//following::input[@type='text'][1]"),
                                                        (By.ID, "ctl00_ContentPlaceHolder1_txtILEP"),
                                                        (By.ID, "ctl00_ContentPlaceHolder1_txtILEPNumber"),
                                                        (By.XPATH, "//input[contains(@id, 'ILEP') and @type='text']"),
                                                        (By.XPATH, "//input[contains(@name, 'ILEP') and @type='text']"),
                                                    ]
                                                    
                                                    ilep_input = None
                                                    for by, selector in ilep_input_selectors:
                                                        try:
                                                            # Use shorter timeout (3 seconds) to check if element exists
                                                            # If not found quickly, try next selector
                                                            quick_wait = WebDriverWait(browser, 3)
                                                            ilep_input = quick_wait.until(EC.presence_of_element_located((by, selector)))
                                                            print(f"[SUCCESS] Found ILEP number input using: {by}={selector}")
                                                            break
                                                        except (TimeoutException, NoSuchElementException):
                                                            print(f"[DEBUG] ILEP number input not found with: {by}={selector}, trying next selector...")
                                                            continue
                                                    
                                                    if ilep_input:
                                                        try:
                                                            # Scroll to input field using safe method
                                                            try:
                                                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_input)
                                                            except Exception as scroll_error:
                                                                # If scrollIntoView fails, try alternative method
                                                                print(f"[DEBUG] scrollIntoView failed, trying alternative: {scroll_error}")
                                                                try:
                                                                    browser.execute_script("arguments[0].scrollIntoView(true);", ilep_input)
                                                                except:
                                                                    # Last resort: use ActionChains
                                                                    from selenium.webdriver.common.action_chains import ActionChains
                                                                    ActionChains(browser).move_to_element(ilep_input).perform()
                                                            time.sleep(0.5)
                                                            
                                                            # Clear existing value and fill
                                                            ilep_input.clear()
                                                            time.sleep(0.2)
                                                            ilep_input.send_keys("0365/0002")
                                                            print("[SUCCESS] Filled ILEP number: 0365/0002")
                                                            
                                                            # Check if input field has PostBack behavior (onchange event)
                                                            try:
                                                                has_ilep_postback = browser.execute_script("""
                                                                    var input = arguments[0];
                                                                    return input.onchange !== null || input.getAttribute('onchange') !== null;
                                                                """, ilep_input)
                                                            except Exception as e_check:
                                                                print(f"[DEBUG] Error checking PostBack: {e_check}")
                                                                has_ilep_postback = False
                                                            
                                                            if has_ilep_postback:
                                                                print("[INFO] ILEP number input has PostBack behavior, waiting for page refresh...")
                                                                # Record current URL before PostBack
                                                                current_url_before = browser.current_url
                                                                print(f"[INFO] Current URL before ILEP PostBack: {current_url_before}")
                                                                
                                                                # Get the input ID before PostBack (element will become stale)
                                                                ilep_input_id = ilep_input.get_attribute("id") or ""
                                                                ilep_input_name = ilep_input.get_attribute("name") or ""
                                                                
                                                                # Trigger change event to initiate PostBack
                                                                try:
                                                                    browser.execute_script("arguments[0].dispatchEvent(new Event('change'));", ilep_input)
                                                                except Exception as e_trigger:
                                                                    print(f"[DEBUG] Error triggering change event: {e_trigger}")
                                                                    # Try alternative: directly set value and trigger
                                                                    try:
                                                                        browser.execute_script("""
                                                                            var input = document.getElementById(arguments[0]) || document.querySelector('[name="' + arguments[1] + '"]');
                                                                            if (input) {
                                                                                input.value = arguments[2];
                                                                                input.dispatchEvent(new Event('change'));
                                                                            }
                                                                        """, ilep_input_id, ilep_input_name, "0365/0002")
                                                                    except:
                                                                        pass
                                                                time.sleep(0.5)
                                                                
                                                                # Wait for PostBack to complete
                                                                print("[INFO] Waiting for PostBack to complete after ILEP number input...")
                                                                try:
                                                                    # Wait for page to start refreshing
                                                                    time.sleep(1)
                                                                    
                                                                    # Wait for document ready state
                                                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                    
                                                                    # Wait for the input field to reappear (page reloaded)
                                                                    # Use the ID or name we saved before PostBack
                                                                    if ilep_input_id:
                                                                        extended_wait.until(EC.presence_of_element_located((By.ID, ilep_input_id)))
                                                                    else:
                                                                        extended_wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'ILEP') and @type='text']")))
                                                                    
                                                                    # Verify we're still on the form page
                                                                    new_url_after = browser.current_url
                                                                    print(f"[INFO] URL after ILEP PostBack: {new_url_after}")
                                                                    
                                                                    if "VisaTypeDetails.aspx" not in new_url_after and "OnlineHome.aspx" in new_url_after:
                                                                        print("[WARN] Page redirected to homepage after ILEP PostBack!")
                                                                        print("[INFO] This might be due to form validation or session timeout")
                                                                        return
                                                                    
                                                                    # Additional wait for dynamic content
                                                                    time.sleep(2)
                                                                    print("[SUCCESS] PostBack completed for ILEP number input")
                                                                    
                                                                    # Check for error page after PostBack
                                                                    check_and_handle_error_page(browser, wait)
                                                                except TimeoutException:
                                                                    print("[WARN] Initial ILEP PostBack wait timeout, continuing to wait until PostBack completes...")
                                                                    # Wait indefinitely until PostBack completes or page redirects
                                                                    postback_completed = False
                                                                    check_count = 0
                                                                    
                                                                    while not postback_completed:
                                                                        try:
                                                                            check_count += 1
                                                                            if check_count % 10 == 0:  # Print status every 10 seconds
                                                                                print(f"[INFO] Still waiting for ILEP PostBack to complete... (checked {check_count} times)")
                                                                            
                                                                            # Check document ready state
                                                                            ready_state = browser.execute_script("return document.readyState")
                                                                            current_url_check = browser.current_url
                                                                            
                                                                            # If redirected to homepage, restart from homepage
                                                                            if "OnlineHome.aspx" in current_url_check:
                                                                                log_operation("ILEP Number", "WARN", "Page redirected to homepage during ILEP PostBack wait - restarting from homepage")
                                                                                # Restart from homepage instead of continuing form filling
                                                                                if restart_from_homepage(browser, wait):
                                                                                    log_operation("ILEP Number", "INFO", "Successfully restarted from homepage, stopping form filling to restart process")
                                                                                    return
                                                                                else:
                                                                                    log_operation("ILEP Number", "ERROR", "Failed to restart from homepage, stopping form filling")
                                                                                    return
                                                                            
                                                                            # Check if we're still on form page
                                                                            if "VisaTypeDetails.aspx" in current_url_check:
                                                                                # Check if ILEP field is present
                                                                                try:
                                                                                    ilep_field_found = browser.find_elements(By.XPATH, "//input[contains(@id, 'ILEP')]")
                                                                                    if ready_state == "complete" and ilep_field_found:
                                                                                        print("[SUCCESS] ILEP PostBack completed after extended wait")
                                                                                        postback_completed = True
                                                                                        time.sleep(2)  # Additional wait for dynamic content
                                                                                        break
                                                                                except:
                                                                                    pass
                                                                            
                                                                            time.sleep(1)  # Check every second
                                                                        except Exception as e:
                                                                            print(f"[DEBUG] Error checking page state: {e}")
                                                                            time.sleep(1)
                                                                except Exception as e:
                                                                    print(f"[WARN] Error waiting for ILEP PostBack: {e}")
                                                                    # Clear ilep_input reference since it might be stale
                                                                    ilep_input = None
                                                                    time.sleep(2)
                                                            else:
                                                                # No PostBack, just a short wait
                                                                time.sleep(0.5)
                                                        except Exception as e_fill:
                                                            print(f"[WARN] Error filling ILEP input field: {e_fill}")
                                                            # Clear reference to avoid using stale element
                                                            ilep_input = None
                                                            import traceback
                                                            traceback.print_exc()
                                                    else:
                                                        print("[WARN] ILEP number input field not found, but checkbox was found")
                                                        print("[INFO] This might mean the input field appears after checking the checkbox, or it has a different selector")
                                                        # Try to find input field again after a short wait (might need PostBack)
                                                        print("[INFO] Waiting 2 seconds and searching for ILEP input field again...")
                                                        time.sleep(2)
                                                        
                                                        # Try alternative search methods
                                                        try:
                                                            # Search for any text input that might be ILEP field
                                                            all_text_inputs = browser.find_elements(By.XPATH, "//input[@type='text']")
                                                            print(f"[DEBUG] Found {len(all_text_inputs)} text inputs on page")
                                                            
                                                            # Try to find input by checking nearby elements or attributes
                                                            for input_elem in all_text_inputs:
                                                                try:
                                                                    if input_elem.is_displayed():
                                                                        input_id = input_elem.get_attribute("id") or ""
                                                                        input_name = input_elem.get_attribute("name") or ""
                                                                        input_class = input_elem.get_attribute("class") or ""
                                                                        
                                                                        # Check if it contains ILEP in any attribute
                                                                        if ("ILEP" in input_id.upper() or 
                                                                            "ILEP" in input_name.upper() or
                                                                            (input_id and "StudyEnglish" in input_id)):
                                                                            ilep_input = input_elem
                                                                            print(f"[SUCCESS] Found ILEP input by searching all inputs: id={input_id}, name={input_name}")
                                                                            break
                                                                except Exception as e_inner:
                                                                    continue
                                                            
                                                            if ilep_input:
                                                                try:
                                                                    # Scroll to input field using safe method
                                                                    try:
                                                                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_input)
                                                                    except Exception as scroll_error:
                                                                        # If scrollIntoView fails, try alternative method
                                                                        print(f"[DEBUG] scrollIntoView failed, trying alternative: {scroll_error}")
                                                                        try:
                                                                            browser.execute_script("arguments[0].scrollIntoView(true);", ilep_input)
                                                                        except:
                                                                            # Last resort: use ActionChains
                                                                            from selenium.webdriver.common.action_chains import ActionChains
                                                                            ActionChains(browser).move_to_element(ilep_input).perform()
                                                                    time.sleep(0.5)
                                                                    
                                                                    # Clear existing value and fill
                                                                    ilep_input.clear()
                                                                    time.sleep(0.2)
                                                                    ilep_input.send_keys("0365/0002")
                                                                    print("[SUCCESS] Filled ILEP number: 0365/0002")
                                                                    
                                                                    # Get input ID/name before checking PostBack (element might become stale)
                                                                    ilep_input_id = ilep_input.get_attribute("id") or ""
                                                                    ilep_input_name = ilep_input.get_attribute("name") or ""
                                                                    
                                                                    # Check for PostBack
                                                                    try:
                                                                        has_ilep_postback = browser.execute_script("""
                                                                            var input = arguments[0];
                                                                            return input.onchange !== null || input.getAttribute('onchange') !== null;
                                                                        """, ilep_input)
                                                                    except Exception as e_check:
                                                                        print(f"[DEBUG] Error checking PostBack: {e_check}")
                                                                        has_ilep_postback = False
                                                                    
                                                                    if has_ilep_postback:
                                                                        print("[INFO] ILEP input has PostBack, waiting...")
                                                                        current_url_before = browser.current_url
                                                                        
                                                                        # Trigger change event
                                                                        try:
                                                                            browser.execute_script("arguments[0].dispatchEvent(new Event('change'));", ilep_input)
                                                                        except Exception as e_trigger:
                                                                            print(f"[DEBUG] Error triggering change event: {e_trigger}")
                                                                            # Try alternative: directly set value and trigger using ID/name
                                                                            try:
                                                                                browser.execute_script("""
                                                                                    var input = document.getElementById(arguments[0]) || document.querySelector('[name="' + arguments[1] + '"]');
                                                                                    if (input) {
                                                                                        input.value = arguments[2];
                                                                                        input.dispatchEvent(new Event('change'));
                                                                                    }
                                                                                """, ilep_input_id, ilep_input_name, "0365/0002")
                                                                            except:
                                                                                pass
                                                                        
                                                                        # Clear reference since element will become stale after PostBack
                                                                        ilep_input = None
                                                                        
                                                                        time.sleep(1)
                                                                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                        time.sleep(2)
                                                                        print("[SUCCESS] PostBack completed for ILEP number input")
                                                                    else:
                                                                        time.sleep(0.5)
                                                                except Exception as e_fill_alt:
                                                                    print(f"[WARN] Error filling ILEP input in alternative search: {e_fill_alt}")
                                                                    ilep_input = None
                                                                    import traceback
                                                                    traceback.print_exc()
                                                            else:
                                                                print("[WARN] Could not find ILEP input field even after searching all text inputs")
                                                                print("[INFO] The field might not be visible yet, or might require a different action")
                                                        except Exception as e_search:
                                                            print(f"[DEBUG] Error searching for ILEP input: {e_search}")
                                                else:
                                                    print("[INFO] ILEP number field not found (may not be required or not yet visible)")
                                                    print("[INFO] This field might only appear for certain Study Type selections (e.g., 'English Language (ILEP)')")
                                                    print("[INFO] Continuing with form filling...")
                                            except Exception as e:
                                                print(f"[WARN] Error filling ILEP number field: {e}")
                                                import traceback
                                                traceback.print_exc()
                                                # Continue anyway as this field might not always be required
                                            
                                        except TimeoutException:
                                            print("[WARN] Initial PostBack wait timeout for Study Type, continuing to wait until PostBack completes...")
                                            # Wait indefinitely until PostBack completes or page redirects
                                            postback_completed = False
                                            check_count = 0
                                            
                                            while not postback_completed:
                                                try:
                                                    check_count += 1
                                                    if check_count % 10 == 0:  # Print status every 10 seconds
                                                        print(f"[INFO] Still waiting for Study Type PostBack to complete... (checked {check_count} times)")
                                                    
                                                    # Check for error page first (before checking other states)
                                                    error_result = check_and_handle_error_page(browser, wait)
                                                    if error_result == "homepage_redirect":
                                                        log_operation("Study Type PostBack", "WARN", "Error page redirected to homepage during PostBack wait - returning homepage_redirect")
                                                        return "homepage_redirect"
                                                    elif error_result == True:
                                                        log_operation("Study Type PostBack", "WARN", "Error page detected during PostBack wait - checking URL after handling...")
                                                        # Wait a bit to see if error page handling resolved the issue
                                                        time.sleep(3)
                                                        error_url_after = browser.current_url
                                                        if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after:
                                                            log_operation("Study Type PostBack", "WARN", "Still on error page after handling - returning homepage_redirect")
                                                            return "homepage_redirect"
                                                        elif "OnlineHome.aspx" in error_url_after:
                                                            log_operation("Study Type PostBack", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                                            return "homepage_redirect"
                                                        elif "VisaTypeDetails.aspx" in error_url_after:
                                                            log_operation("Study Type PostBack", "INFO", "Error page redirected back to form page - continuing")
                                                            # Continue with normal PostBack wait
                                                        else:
                                                            log_operation("Study Type PostBack", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                                            return "homepage_redirect"
                                                    
                                                    # Check document ready state
                                                    ready_state = browser.execute_script("return document.readyState")
                                                    current_url_check = browser.current_url
                                                    
                                                    # Check for error page URL
                                                    if "ApplicationError.aspx" in current_url_check or "Error.aspx" in current_url_check:
                                                        log_operation("Study Type PostBack", "ERROR", f"Detected error page URL during PostBack wait: {current_url_check}")
                                                        error_result = check_and_handle_error_page(browser, wait)
                                                        if error_result == "homepage_redirect":
                                                            log_operation("Study Type PostBack", "WARN", "Error page redirected to homepage - returning homepage_redirect")
                                                            return "homepage_redirect"
                                                        elif error_result == True:
                                                            time.sleep(3)
                                                            error_url_after = browser.current_url
                                                            if "ApplicationError.aspx" in error_url_after or "Error" in error_url_after or "OnlineHome.aspx" in error_url_after:
                                                                log_operation("Study Type PostBack", "WARN", "Error page detected or redirected to homepage - returning homepage_redirect")
                                                                return "homepage_redirect"
                                                            elif "VisaTypeDetails.aspx" in error_url_after:
                                                                log_operation("Study Type PostBack", "INFO", "Error page redirected back to form page - continuing")
                                                                # Continue with normal PostBack wait
                                                            else:
                                                                log_operation("Study Type PostBack", "WARN", f"Unexpected URL after error page: {error_url_after} - returning homepage_redirect")
                                                                return "homepage_redirect"
                                                    
                                                    # If redirected to homepage, wait to see if it redirects back
                                                    if "OnlineHome.aspx" in current_url_check:
                                                        log_operation("Study Type PostBack", "WARN", "Detected redirect to homepage during PostBack wait")
                                                        log_operation("Study Type PostBack", "INFO", "Waiting 5 seconds to see if page automatically redirects back to form...")
                                                        time.sleep(5)
                                                        
                                                        # Check again after waiting
                                                        check_url_after_wait = browser.current_url
                                                        if "VisaTypeDetails.aspx" in check_url_after_wait:
                                                            log_operation("Study Type PostBack", "SUCCESS", "Page automatically redirected back to form page")
                                                            # Wait for element to be present
                                                            try:
                                                                extended_wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'StudyType') or contains(@id, 'studyType')]")))
                                                                ready_state_after = browser.execute_script("return document.readyState")
                                                                if ready_state_after == "complete":
                                                                    log_operation("Study Type PostBack", "SUCCESS", "PostBack completed after redirect back to form")
                                                                    postback_completed = True
                                                                    time.sleep(2)
                                                                    break
                                                            except:
                                                                pass
                                                        elif "OnlineHome.aspx" in check_url_after_wait:
                                                            log_operation("Study Type PostBack", "WARN", "Still on homepage after waiting, attempting to navigate back to form page...")
                                                            try:
                                                                browser.get("https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx")
                                                                time.sleep(3)
                                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                
                                                                verify_url = browser.current_url
                                                                if "VisaTypeDetails.aspx" in verify_url:
                                                                    log_operation("Study Type PostBack", "SUCCESS", "Successfully navigated back to form page")
                                                                    log_operation("Study Type PostBack", "INFO", "Re-filling previously filled fields...")
                                                                    
                                                                    # Re-fill the fields that were already filled
                                                                    try:
                                                                        # Re-fill Country
                                                                        country_select = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlCountryOfNationality")))
                                                                        Select(country_select).select_by_visible_text("People's Republic of China")
                                                                        log_operation("Study Type PostBack Recovery", "SUCCESS", "Re-filled Country Of Nationality")
                                                                        time.sleep(POSTBACK_BETWEEN_DELAY)
                                                                        
                                                                        # Re-fill Reason
                                                                        reason_select = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlVisaCategory")))
                                                                        Select(reason_select).select_by_visible_text("Study")
                                                                        log_operation("Study Type PostBack Recovery", "SUCCESS", "Re-filled Reason for travel")
                                                                        time.sleep(POSTBACK_BETWEEN_DELAY)
                                                                        
                                                                        # Wait for Study Type to appear and re-select
                                                                        time.sleep(2)
                                                                        study_type_select = extended_wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'StudyType') or contains(@id, 'studyType')]")))
                                                                        Select(study_type_select).select_by_visible_text("English Language (ILEP)")
                                                                        log_operation("Study Type PostBack Recovery", "SUCCESS", "Re-filled Study Type")
                                                                        time.sleep(POSTBACK_BETWEEN_DELAY)
                                                                        
                                                                        postback_completed = True
                                                                        break
                                                                    except Exception as refill_error:
                                                                        log_operation("Study Type PostBack Recovery", "ERROR", f"Error re-filling fields: {refill_error}")
                                                                        return
                                                                else:
                                                                    log_operation("Study Type PostBack", "ERROR", "Failed to navigate back to form page - returning False to trigger restart")
                                                                    return False
                                                            except Exception as nav_error:
                                                                log_operation("Study Type PostBack", "ERROR", f"Error navigating back to form page: {nav_error} - returning False to trigger restart")
                                                                return False
                                                    
                                                    # Check if we're still on form page
                                                    if "VisaTypeDetails.aspx" in current_url_check:
                                                        # Check if key elements are present
                                                        try:
                                                            # Try to find Study Type dropdown or ILEP field
                                                            study_type_found = browser.find_elements(By.XPATH, "//select[contains(@id, 'StudyType') or contains(@id, 'studyType')]")
                                                            ilep_field_found = browser.find_elements(By.XPATH, "//input[contains(@id, 'ILEP')]")
                                                            
                                                            if ready_state == "complete" and (study_type_found or ilep_field_found):
                                                                print("[SUCCESS] PostBack completed after extended wait")
                                                                postback_completed = True
                                                                time.sleep(2)  # Additional wait for dynamic content
                                                                break
                                                        except:
                                                            pass
                                                    
                                                    time.sleep(1)  # Check every second
                                                except Exception as e:
                                                    print(f"[DEBUG] Error checking page state: {e}")
                                                    time.sleep(1)
                                        except Exception as e:
                                            print(f"[WARN] Error waiting for Study Type PostBack: {e}")
                                            # Check page state before continuing
                                            try:
                                                current_url_check = browser.current_url
                                                if "OnlineHome.aspx" in current_url_check:
                                                    print("[ERROR] Page redirected to homepage - stopping form filling")
                                                    return
                                            except:
                                                pass
                                            time.sleep(2)
                                    else:
                                        # Short wait if no PostBack
                                        time.sleep(0.5)
                                    
                                    break
                                except:
                                    continue
                            
                            if not selected_study_type:
                                # Try to get available options
                                try:
                                    options = select.options
                                    available_options = [opt.text for opt in options if opt.text.strip() and opt.text.strip() != "--Select--"]
                                    if available_options:
                                        print(f"[INFO] Available Study Type options: {available_options[:5]}")
                                        # Select first non-empty option
                                        for opt in options:
                                            if opt.text.strip() and opt.text.strip() != "--Select--":
                                                select.select_by_visible_text(opt.text)
                                                print(f"[SUCCESS] Selected '{opt.text}' for Study Type (first available)")
                                                selected_study_type = True
                                                
                                                # Wait for PostBack if needed
                                                if has_postback:
                                                    print("[INFO] Waiting for PostBack to complete...")
                                                    try:
                                                        time.sleep(1)
                                                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                        if study_type_id:
                                                            extended_wait.until(EC.presence_of_element_located((By.ID, study_type_id)))
                                                        time.sleep(2)
                                                        print("[SUCCESS] PostBack completed for Study Type")
                                                        
                                                        # After Study Type PostBack, fill ILEP number field if it appears
                                                        try:
                                                            print("[INFO] Checking for ILEP number field after Study Type PostBack...")
                                                            time.sleep(1)
                                                            
                                                            ilep_checkbox_selectors = [
                                                                (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyEnglishILEP']//input[@type='checkbox']"),
                                                                (By.XPATH, "//*[contains(text(), 'I know my ILEP number')]//preceding::input[@type='checkbox'][1]"),
                                                                (By.XPATH, "//label[contains(text(), 'I know my ILEP number')]//following::input[@type='checkbox'][1]"),
                                                                (By.ID, "ctl00_ContentPlaceHolder1_chkILEP"),
                                                                (By.XPATH, "//input[contains(@id, 'ILEP') and @type='checkbox']"),
                                                            ]
                                                            
                                                            ilep_checkbox = None
                                                            for by, selector in ilep_checkbox_selectors:
                                                                try:
                                                                    ilep_checkbox = extended_wait.until(EC.presence_of_element_located((by, selector)))
                                                                    break
                                                                except:
                                                                    continue
                                                            
                                                            if ilep_checkbox:
                                                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_checkbox)
                                                                time.sleep(0.5)
                                                                if not ilep_checkbox.is_selected():
                                                                    ilep_checkbox.click()
                                                                    print("[SUCCESS] Checked 'I know my ILEP number' checkbox")
                                                                    time.sleep(0.5)
                                                                
                                                                ilep_input_selectors = [
                                                                    (By.XPATH, "//tr[@id='ctl00_ContentPlaceHolder1_tr_StudyEnglishILEP']//input[@type='text']"),
                                                                    (By.XPATH, "//*[contains(text(), 'I know my ILEP number')]//following::input[@type='text'][1]"),
                                                                    (By.ID, "ctl00_ContentPlaceHolder1_txtILEP"),
                                                                    (By.XPATH, "//input[contains(@id, 'ILEP') and @type='text']"),
                                                                ]
                                                                
                                                                ilep_input = None
                                                                for by, selector in ilep_input_selectors:
                                                                    try:
                                                                        ilep_input = extended_wait.until(EC.presence_of_element_located((by, selector)))
                                                                        break
                                                                    except:
                                                                        continue
                                                                
                                                                if ilep_input:
                                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", ilep_input)
                                                                    time.sleep(0.5)
                                                                    ilep_input.clear()
                                                                    time.sleep(0.2)
                                                                    ilep_input.send_keys("0365/0002")
                                                                    print("[SUCCESS] Filled ILEP number: 0365/0002")
                                                                    
                                                                    # Check for PostBack
                                                                    has_ilep_postback = browser.execute_script("""
                                                                        var input = arguments[0];
                                                                        return input.onchange !== null || input.getAttribute('onchange') !== null;
                                                                    """, ilep_input)
                                                                    
                                                                    if has_ilep_postback:
                                                                        print("[INFO] ILEP number input has PostBack, waiting...")
                                                                        current_url_before = browser.current_url
                                                                        browser.execute_script("arguments[0].dispatchEvent(new Event('change'));", ilep_input)
                                                                        time.sleep(1)
                                                                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                        new_url_after = browser.current_url
                                                                        if "VisaTypeDetails.aspx" not in new_url_after and "OnlineHome.aspx" in new_url_after:
                                                                            print("[WARN] Page redirected to homepage after ILEP PostBack!")
                                                                            return
                                                                        time.sleep(2)
                                                                        print("[SUCCESS] PostBack completed for ILEP number input")
                                                                    else:
                                                                        time.sleep(0.5)
                                                        except Exception as e:
                                                            print(f"[WARN] Error filling ILEP number field: {e}")
                                                    except:
                                                        time.sleep(2)
                                                else:
                                                    time.sleep(0.5)
                                                break
                                except Exception as e:
                                    print(f"[WARN] Could not get Study Type options: {e}")
                            
                            if not selected_study_type:
                                print("[WARN] Could not select Study Type, but continuing...")
                        else:
                            print("[INFO] Study Type dropdown not found (may not be required or not yet visible)")
                    except Exception as e:
                        print(f"[WARN] Error checking for Study Type field: {e}")
                        # Continue anyway as this field might not always be required
                        
                except TimeoutException:
                    print("[WARN] Initial PostBack wait timeout for reason for travel, continuing to wait until PostBack completes...")
                    # Wait until PostBack completes or page redirects, but stop after 50 checks
                    postback_completed = False
                    check_count = 0
                    max_checks = 50
                    
                    while not postback_completed and check_count < max_checks:
                        try:
                            check_count += 1
                            if check_count % 10 == 0:  # Print status every 10 seconds
                                print(f"[INFO] Still waiting for reason PostBack to complete... (checked {check_count} times)")
                            
                            # Check document ready state
                            ready_state = browser.execute_script("return document.readyState")
                            current_url_check = browser.current_url
                            
                            # If redirected to homepage, return False to trigger restart
                            if "OnlineHome.aspx" in current_url_check:
                                log_operation("Reason for travel", "WARN", "Page redirected to homepage during reason PostBack wait - returning False to trigger restart")
                                return False
                            
                            # Check if we're still on form page
                            if "VisaTypeDetails.aspx" in current_url_check:
                                # Check if key element is present
                                try:
                                    reason_select_found = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_ddlVisaCategory")
                                    if ready_state == "complete" and reason_select_found:
                                        print("[SUCCESS] PostBack completed after extended wait")
                                        postback_completed = True
                                        time.sleep(2)  # Additional wait for dynamic content
                                        break
                                except:
                                    pass
                            
                            time.sleep(1)  # Check every second
                        except Exception as e:
                            print(f"[DEBUG] Error checking page state: {e}")
                            time.sleep(1)
                    
                    # If we've checked 50 times and PostBack still hasn't completed, stop waiting
                    if not postback_completed and check_count >= max_checks:
                        log_operation("Reason for travel", "WARN", f"PostBack wait exceeded {max_checks} checks, stopping wait and refreshing page...")
                        print(f"[WARN] PostBack wait exceeded {max_checks} checks, refreshing page and detecting current state...")
                        
                        # Refresh page
                        browser.refresh()
                        time.sleep(3)
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        time.sleep(2)
                        
                        # Check for homepage redirect after refresh
                        redirect_check = check_homepage_redirect(browser, wait)
                        if redirect_check == "homepage":
                            log_operation("Reason for travel", "WARN", "After refresh, redirected to homepage - returning homepage_redirect")
                            return "homepage_redirect"
                        
                        # Check for error page
                        error_result = check_and_handle_error_page(browser, wait)
                        if error_result == "homepage_redirect":
                            log_operation("Reason for travel", "WARN", "After refresh, error page redirected to homepage - checking for Application Number...")
                            # Check for application number and handle accordingly
                            saved_app_number = get_saved_application_number()
                            if saved_app_number:
                                log_operation("Reason for travel", "INFO", f"Found Application Number: {saved_app_number}, calling retrieve_application...")
                                if retrieve_application(browser, wait, saved_app_number):
                                    log_operation("Reason for travel", "SUCCESS", "Successfully retrieved application after error page handling")
                                    # Detect page after retrieval
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                    page_number = detect_page_number_no_refresh(browser, wait)
                                    if page_number:
                                        return f"form_page_{page_number}"
                                    else:
                                        return "homepage_redirect"
                                else:
                                    log_operation("Reason for travel", "WARN", "Failed to retrieve application, calling restart_from_homepage...")
                                    if restart_from_homepage(browser, wait):
                                        return "homepage_redirect"
                                    else:
                                        return "homepage_redirect"
                            else:
                                log_operation("Reason for travel", "INFO", "No Application Number found, calling restart_from_homepage...")
                                if restart_from_homepage(browser, wait):
                                    return "homepage_redirect"
                                else:
                                    return "homepage_redirect"
                        elif error_result == "application_error":
                            log_operation("Reason for travel", "ERROR", "After refresh, application error detected - navigating to homepage and checking for Application Number...")
                            # Navigate to homepage
                            try:
                                browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                                time.sleep(3)
                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                time.sleep(2)
                            except Exception as e:
                                log_operation("Reason for travel", "ERROR", f"Failed to navigate to homepage: {e}")
                                return "application_error"
                            
                            # Check for application number and handle accordingly
                            saved_app_number = get_saved_application_number()
                            if saved_app_number:
                                log_operation("Reason for travel", "INFO", f"Found Application Number: {saved_app_number}, calling retrieve_application...")
                                if retrieve_application(browser, wait, saved_app_number):
                                    log_operation("Reason for travel", "SUCCESS", "Successfully retrieved application after error page handling")
                                    # Detect page after retrieval
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                    page_number = detect_page_number_no_refresh(browser, wait)
                                    if page_number:
                                        return f"form_page_{page_number}"
                                    else:
                                        return "homepage_redirect"
                                else:
                                    log_operation("Reason for travel", "WARN", "Failed to retrieve application, calling restart_from_homepage...")
                                    if restart_from_homepage(browser, wait):
                                        return "homepage_redirect"
                                    else:
                                        return "homepage_redirect"
                            else:
                                log_operation("Reason for travel", "INFO", "No Application Number found, calling restart_from_homepage...")
                                if restart_from_homepage(browser, wait):
                                    return "homepage_redirect"
                                else:
                                    return "homepage_redirect"
                        elif error_result == True:
                            # Error page still exists after handling, navigate to homepage
                            log_operation("Reason for travel", "WARN", "After refresh, error page still exists - navigating to homepage and checking for Application Number...")
                            try:
                                browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                                time.sleep(3)
                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                time.sleep(2)
                            except Exception as e:
                                log_operation("Reason for travel", "ERROR", f"Failed to navigate to homepage: {e}")
                                return "application_error"
                            
                            # Check for application number and handle accordingly
                            saved_app_number = get_saved_application_number()
                            if saved_app_number:
                                log_operation("Reason for travel", "INFO", f"Found Application Number: {saved_app_number}, calling retrieve_application...")
                                if retrieve_application(browser, wait, saved_app_number):
                                    log_operation("Reason for travel", "SUCCESS", "Successfully retrieved application after error page handling")
                                    # Detect page after retrieval
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                    page_number = detect_page_number_no_refresh(browser, wait)
                                    if page_number:
                                        return f"form_page_{page_number}"
                                    else:
                                        return "homepage_redirect"
                                else:
                                    log_operation("Reason for travel", "WARN", "Failed to retrieve application, calling restart_from_homepage...")
                                    if restart_from_homepage(browser, wait):
                                        return "homepage_redirect"
                                    else:
                                        return "homepage_redirect"
                            else:
                                log_operation("Reason for travel", "INFO", "No Application Number found, calling restart_from_homepage...")
                                if restart_from_homepage(browser, wait):
                                    return "homepage_redirect"
                                else:
                                    return "homepage_redirect"
                        
                        # If error_result is False or a form_page_X, continue with normal detection
                        # Detect current page number
                        page_number = detect_page_number_no_refresh(browser, wait)
                        if page_number:
                            log_operation("Reason for travel", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                            return f"form_page_{page_number}"
                        else:
                            # Retry detection up to 3 times
                            max_retries = 3
                            for retry in range(max_retries):
                                time.sleep(2)
                                page_number = detect_page_number_no_refresh(browser, wait)
                                if page_number:
                                    log_operation("Reason for travel", "INFO", f"After refresh (retry {retry + 1}), detected page {page_number}, returning form_page_{page_number}")
                                    return f"form_page_{page_number}"
                            
                            # If still can't detect page, check for application number and handle accordingly
                            saved_app_number = get_saved_application_number()
                            if saved_app_number:
                                log_operation("Reason for travel", "WARN", f"Could not detect page after refresh, but found Application Number: {saved_app_number}, navigating to homepage and calling retrieve_application...")
                                try:
                                    browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                except Exception as e:
                                    log_operation("Reason for travel", "ERROR", f"Failed to navigate to homepage: {e}")
                                    return "homepage_redirect"
                                
                                if retrieve_application(browser, wait, saved_app_number):
                                    log_operation("Reason for travel", "SUCCESS", "Successfully retrieved application")
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                    page_number = detect_page_number_no_refresh(browser, wait)
                                    if page_number:
                                        return f"form_page_{page_number}"
                                    else:
                                        return "homepage_redirect"
                                else:
                                    log_operation("Reason for travel", "WARN", "Failed to retrieve application, calling restart_from_homepage...")
                                    if restart_from_homepage(browser, wait):
                                        return "homepage_redirect"
                                    else:
                                        return "homepage_redirect"
                            else:
                                log_operation("Reason for travel", "WARN", "Could not detect page after refresh and no Application Number found, navigating to homepage and calling restart_from_homepage...")
                                try:
                                    browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                                    time.sleep(3)
                                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                    time.sleep(2)
                                except Exception as e:
                                    log_operation("Reason for travel", "ERROR", f"Failed to navigate to homepage: {e}")
                                    return "homepage_redirect"
                                
                                if restart_from_homepage(browser, wait):
                                    return "homepage_redirect"
                                else:
                                    return "homepage_redirect"
            else:
                time.sleep(1)
        except Exception as e:
            print(f"[WARN] Could not fill reason for travel by ID: {e}")
            fill_dropdown_by_label(browser, wait, "What is the reason for travel", "Study")
        
        # 3. What type of Visa/Preclearance are you applying for? - Radio button
        try:
            visa_type_radio = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_rdblstVisaStayType_1")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", visa_type_radio)
            time.sleep(0.5)
            if not visa_type_radio.is_selected():
                visa_type_radio.click()
                print("[SUCCESS] Selected 'Long Stay (D)' for Visa type")
            else:
                print("[INFO] 'Long Stay (D)' already selected")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not select visa type by ID: {e}")
            select_radio_by_label(browser, wait, "What type of Visa/Preclearance are you applying for", "Long Stay (D)")
        
        # 4. Journey Type - Radio button
        try:
            journey_radio = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_rdblstJourney_1")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", journey_radio)
            time.sleep(0.5)
            if not journey_radio.is_selected():
                journey_radio.click()
                print("[SUCCESS] Selected 'Multiple' for Journey Type")
            else:
                print("[INFO] 'Multiple' already selected")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not select journey type by ID: {e}")
            select_radio_by_label(browser, wait, "Journey Type", "Multiple")
        
        # 5. Passport Type - using direct ID
        try:
            passport_type_select = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_ddlPassportType")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", passport_type_select)
            time.sleep(0.5)
            select = Select(passport_type_select)
            select.select_by_visible_text("National Passport")
            print("[SUCCESS] Selected 'National Passport' for Passport Type")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not fill Passport Type by ID: {e}")
            # Fallback to label-based method
            fill_dropdown_by_label(browser, wait, "Passport Type", "National Passport")
        
        # 6. Passport/Travel Document Number - using direct ID
        try:
            passport_no_input = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtPassportNo")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", passport_no_input)
            time.sleep(0.5)
            passport_no_input.clear()
            passport_no_input.send_keys("112223")
            print("[SUCCESS] Filled '112223' in Passport/Travel Document Number")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not fill passport number by ID: {e}")
            fill_text_by_label(browser, wait, "Passport/Travel Document Number", "112223")
        
        # 7. Proposed dates - From - using direct ID
        try:
            entry_date_input = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtEntryDate")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", entry_date_input)
            time.sleep(0.5)
            # Clear the placeholder text first
            entry_date_input.clear()
            time.sleep(0.2)
            entry_date_input.send_keys("01/03/2026")
            print("[SUCCESS] Filled '01/03/2026' in Entry Date (From)")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not fill entry date by ID: {e}")
            fill_date_by_label(browser, wait, "Proposed dates you wish to enter and leave Ireland", "From", "01/03/2026")
        
        # 8. Proposed dates - To - using direct ID
        try:
            exit_date_input = extended_wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtExitDate")))
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", exit_date_input)
            time.sleep(0.5)
            # Clear the placeholder text first
            exit_date_input.clear()
            time.sleep(0.2)
            exit_date_input.send_keys("08/03/2026")
            print("[SUCCESS] Filled '08/03/2026' in Exit Date (To)")
            time.sleep(0.5)
        except Exception as e:
            print(f"[WARN] Could not fill exit date by ID: {e}")
            fill_date_by_label(browser, wait, "Proposed dates you wish to enter and leave Ireland", "To", "08/03/2026")
        
        log_operation("fill_page_1", "SUCCESS", "Page 1 filled successfully")
        
        # Final verification before proceeding
        if verify_page_state(browser, wait, 
                           expected_url_pattern="VisaTypeDetails.aspx",
                           operation_name="fill_page_1 (final)"):
            log_operation("fill_page_1", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
        else:
            log_operation("fill_page_1", "WARN", "Page state verification failed, but proceeding to click button...")
        
        # Click Next/Continue button to go to next page
        if screenshots_dir:
            take_screenshot(browser, f"page_1_filled", output_dir=screenshots_dir)
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_1", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_1", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_1", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_1", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_1", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_1", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_1", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_1", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # Return True to indicate successful completion (if no redirect)
        return True
        
    except Exception as e:
        print(f"[ERROR] Error filling Page 1: {e}")
        import traceback
        traceback.print_exc()
        # Check if we're on homepage (which means we should restart)
        try:
            current_url = browser.current_url
            if "OnlineHome.aspx" in current_url:
                log_operation("fill_page_1", "WARN", "On homepage after error - returning False to trigger restart")
                return False
        except:
            pass
        return False




