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

def fill_page_9(browser, wait):
    """
    Fill the ninth page of the application form
    
    Fields to fill:
    Course of Study in Ireland:
    - Have you been accepted on a course of study in Ireland?: Yes
    - Name of College: Greenfield English College
    - Course Title: General English Course (GEC)
    - Duration of Course: 25 weeks
    - From: 26/01/2026
    - To: 17/07/2026
    - Have you paid your course fees in full (1st Year)?: Yes
    - Hours of organized daytime tuition per week: 18.25 hours
    
    Previous Study / Language Ability:
    - Have you studied in Ireland before?: No
    - Do you speak English?: Yes
    
    English Language Qualifications:
    - Test Taken: IELTS Academic, Date: 15/09/2024, Overall Result: 5.5
    - Test Taken: Duolingo English Test, Date: 20/11/2024, Overall Result: 95
    
    Educational Qualifications:
    - School: Hangzhou No.2 High School, From: 01/09/2020 To: 30/06/2023, Qualification: High School Diploma
    - School: Zhejiang Technical Institute, From: 01/09/2023 To: 30/06/2024, Qualification: Foundation Studies Certificate
    
    Gaps in Education:
    - Explanation: From July 2024 to December 2025, the applicant focused on English language preparation...
    
    Previous Employment:
    - Name of Employer: None, Date: N/A, Position: N/A
    
    Financial Support:
    - How will your studies be supported financially?: Self
    - Details of any other funds: Personal savings and family financial support...
    """
    log_operation("fill_page_9", "INFO", "Starting to fill Page 9...")
    
    try:
        # Check for homepage redirect before starting
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Already on homepage before starting Page 9, stopping...")
            return "homepage_redirect"
        
        # Verify page state before starting
        time.sleep(OPERATION_DELAY * 2)  # Wait a bit longer for page 9 to load
        
        # Check for homepage redirect after wait
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Redirected to homepage during initial wait, stopping...")
            return "homepage_redirect"
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            log_operation("fill_page_9", "INFO", "Page 9 document ready")
        except:
            log_operation("fill_page_9", "WARN", "Document ready state check timeout, continuing anyway...")
        
        # Check again after document ready
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Redirected to homepage after document ready, stopping...")
            return "homepage_redirect"
        
        # Check for Application Number when entering page (Application Number may appear from page 3 onwards)
        time.sleep(1)  # Small delay to ensure page is fully loaded
        application_number = extract_application_number(browser, wait, save_debug=True)
        if application_number:
            log_operation("fill_page_9", "SUCCESS", f"Application Number detected when entering Page 9: {application_number}")
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
                        log_operation(f"fill_page_9", "INFO", f"Field {field_id} already has value '{current_value}', skipping...")
                        return True
                
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)
                
                if field_type == "text" or field_type == "textarea":
                    element.clear()
                    time.sleep(0.2)
                    element.send_keys(value)
                    log_operation(f"fill_page_9", "SUCCESS", f"Filled {field_id} with '{value}'")
                elif field_type == "radio":
                    if not element.is_selected():
                        element.click()
                        log_operation(f"fill_page_9", "SUCCESS", f"Selected radio {field_id}")
                    else:
                        log_operation(f"fill_page_9", "INFO", f"Radio {field_id} already selected, skipping...")
                
                return True
            except Exception as e:
                log_operation(f"fill_page_9", "WARN", f"Error filling {field_id}: {e}")
                return False
        
        # ===== MANDATORY FIELDS ONLY (marked with *) =====
        # 1. Have you been accepted on a course of study in Ireland? * (MANDATORY)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("Accepted on course", "INFO", "Selecting accepted on course (MANDATORY)...")
            
            # Get current URL before clicking
            url_before = browser.current_url
            
            # Click the radio button
            fill_field_by_id("ctl00_ContentPlaceHolder1_rdblstAcceptedByCollege_0", "Yes", "radio", check_filled=False)
            
            # Wait for PostBack to complete - wait for URL change or page update
            log_operation("Accepted on course", "INFO", "Waiting for PostBack to complete...")
            try:
                # Wait for URL to change (indicating PostBack)
                WebDriverWait(browser, 10).until(
                    lambda driver: driver.current_url != url_before
                )
                log_operation("Accepted on course", "SUCCESS", f"URL changed after PostBack: {browser.current_url}")
            except:
                log_operation("Accepted on course", "INFO", "URL did not change, waiting for page update...")
            
            # Wait for page to be ready
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            # After selecting "Yes", check if conditional mandatory fields appear
            log_operation("Accepted on course", "INFO", "Checking for conditional mandatory fields after selecting 'Yes'...")
            # Wait for PostBack to complete - check for AJAX completion and field appearance
            max_wait_time = 20  # Increased to 20 seconds
            wait_interval = 0.5  # Check every 0.5 seconds
            waited_time = 0
            fields_appeared = False
            
            while waited_time < max_wait_time:
                try:
                    # Check if course fields are now present in the DOM
                    course_title_element = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtCourseTitle")
                    course_duration_element = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtCourseDuration")
                    course_from_element = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtCourseDurationfrom")
                    name_college_element = browser.find_elements(By.ID, "ctl00_ContentPlaceHolder1_txtNameOfCollege")
                    
                    # Also check page source
                    page_source = browser.page_source
                    has_text = "Course Title" in page_source or "Name of College" in page_source or "Duration of course" in page_source
                    
                    if course_title_element or course_duration_element or course_from_element or name_college_element or has_text:
                        log_operation("Accepted on course", "SUCCESS", f"Course fields appeared after {waited_time} seconds")
                        fields_appeared = True
                        break
                except Exception as e:
                    log_operation("Accepted on course", "DEBUG", f"Error checking for fields: {e}")
                
                time.sleep(wait_interval)
                waited_time += wait_interval
            
            if not fields_appeared:
                log_operation("Accepted on course", "WARN", f"Course fields did not appear after {max_wait_time} seconds, but continuing anyway...")
            
            # Wait for page to be ready again
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check page source for course-related fields
            try:
                page_source = browser.page_source
                has_course_fields = ("Name of College" in page_source or "Course Title" in page_source or 
                                   "Duration of course" in page_source or 
                                   "ctl00_ContentPlaceHolder1_txtCourseTitle" in page_source or
                                   "ctl00_ContentPlaceHolder1_txtCourseDuration" in page_source or
                                   "ctl00_ContentPlaceHolder1_txtNameOfCollege" in page_source)
                
                if has_course_fields:
                    log_operation("Course fields", "INFO", "Found course-related fields, attempting to fill...")
                    
                    # Fill Name of College - try multiple strategies
                    name_college_filled = False
                    name_college_selectors = [
                        ("label", "Name of College"),
                        ("id", "ctl00_ContentPlaceHolder1_txtNameOfCollege"),
                        ("xpath", "//input[contains(@id, 'NameOfCollege') or contains(@name, 'NameOfCollege')]"),
                        ("xpath", "//textarea[contains(@id, 'NameOfCollege') or contains(@name, 'NameOfCollege')]"),
                        ("xpath", "//input[contains(@id, 'College') and contains(@id, 'Name')]"),
                        ("xpath", "//textarea[contains(@id, 'College') and contains(@id, 'Name')]"),
                    ]
                    for strategy, selector in name_college_selectors:
                        try:
                            if strategy == "label":
                                fill_text_by_label(browser, wait, selector, "Greenfield English College")
                                name_college_filled = True
                                log_operation("Name of College", "SUCCESS", f"Filled using label: {selector}")
                                break
                            elif strategy == "id":
                                fill_field_by_id(selector, "Greenfield English College", "text")
                                name_college_filled = True
                                log_operation("Name of College", "SUCCESS", f"Filled using ID: {selector}")
                                break
                            else:  # xpath
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("Greenfield English College")
                                name_college_filled = True
                                log_operation("Name of College", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                        except Exception as e:
                            log_operation("Name of College", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not name_college_filled:
                        log_operation("Name of College", "WARN", "Could not fill Name of College using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Fill Course Title - try multiple strategies, prioritize direct ID
                    course_title_filled = False
                    course_title_selectors = [
                        ("id", "ctl00_ContentPlaceHolder1_txtCourseTitle"),
                        ("xpath", "//input[@id='ctl00_ContentPlaceHolder1_txtCourseTitle']"),
                        ("xpath", "//input[contains(@id, 'CourseTitle') or contains(@name, 'CourseTitle')]"),
                        ("xpath", "//textarea[contains(@id, 'CourseTitle') or contains(@name, 'CourseTitle')]"),
                        ("xpath", "//input[contains(@id, 'Course') and contains(@id, 'Title')]"),
                        ("xpath", "//textarea[contains(@id, 'Course') and contains(@id, 'Title')]"),
                        ("label", "Course Title"),
                    ]
                    for strategy, selector in course_title_selectors:
                        try:
                            if strategy == "id":
                                # Try direct ID first with explicit wait and retry
                                for retry in range(3):
                                    try:
                                        element = extended_wait.until(EC.presence_of_element_located((By.ID, selector)))
                                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                        time.sleep(0.3)
                                        element.clear()
                                        time.sleep(0.2)
                                        element.send_keys("General English Course (GEC)")
                                        # Verify the value was set
                                        verify_value = element.get_attribute("value")
                                        if "General English Course" in verify_value or verify_value == "General English Course (GEC)":
                                            course_title_filled = True
                                            log_operation("Course Title", "SUCCESS", f"Filled using ID: {selector} (verified: {verify_value})")
                                            break
                                        else:
                                            log_operation("Course Title", "DEBUG", f"Value not set correctly on retry {retry+1}, expected 'General English Course (GEC)', got '{verify_value}'")
                                    except Exception as e:
                                        if retry < 2:
                                            log_operation("Course Title", "DEBUG", f"Retry {retry+1} failed: {e}, retrying...")
                                            time.sleep(1)
                                            continue
                                        else:
                                            raise
                                if course_title_filled:
                                    break
                            elif strategy == "xpath":
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("General English Course (GEC)")
                                course_title_filled = True
                                log_operation("Course Title", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                            else:  # label
                                fill_text_by_label(browser, wait, selector, "General English Course (GEC)")
                                course_title_filled = True
                                log_operation("Course Title", "SUCCESS", f"Filled using label: {selector}")
                                break
                        except Exception as e:
                            log_operation("Course Title", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not course_title_filled:
                        log_operation("Course Title", "WARN", "Could not fill Course Title using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Fill Duration of course - try multiple strategies, prioritize direct ID
                    duration_filled = False
                    duration_selectors = [
                        ("id", "ctl00_ContentPlaceHolder1_txtCourseDuration"),
                        ("xpath", "//input[@id='ctl00_ContentPlaceHolder1_txtCourseDuration']"),
                        ("xpath", "//input[contains(@id, 'CourseDuration') or contains(@name, 'CourseDuration')]"),
                        ("xpath", "//textarea[contains(@id, 'CourseDuration') or contains(@name, 'CourseDuration')]"),
                        ("xpath", "//input[contains(@id, 'Duration') and contains(@id, 'Course')]"),
                        ("xpath", "//textarea[contains(@id, 'Duration') and contains(@id, 'Course')]"),
                        ("label", "Duration of course"),
                    ]
                    for strategy, selector in duration_selectors:
                        try:
                            if strategy == "id":
                                # Try direct ID first with explicit wait
                                element = extended_wait.until(EC.presence_of_element_located((By.ID, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("25 weeks")
                                duration_filled = True
                                log_operation("Duration of course", "SUCCESS", f"Filled using ID: {selector}")
                                break
                            elif strategy == "xpath":
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("25 weeks")
                                duration_filled = True
                                log_operation("Duration of course", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                            else:  # label
                                fill_text_by_label(browser, wait, selector, "25 weeks")
                                duration_filled = True
                                log_operation("Duration of course", "SUCCESS", f"Filled using label: {selector}")
                                break
                        except Exception as e:
                            log_operation("Duration of course", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not duration_filled:
                        log_operation("Duration of course", "WARN", "Could not fill Duration of course using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Fill Course From date - try multiple strategies
                    course_from_filled = False
                    course_from_selectors = [
                        ("id", "ctl00_ContentPlaceHolder1_txtCourseDurationfrom"),
                        ("xpath", "//input[contains(@id, 'CourseDurationfrom') or contains(@name, 'CourseDurationfrom')]"),
                        ("xpath", "//input[contains(@id, 'Course') and contains(@id, 'Duration') and contains(@id, 'from')]"),
                        ("label", "From"),
                    ]
                    for strategy, selector in course_from_selectors:
                        try:
                            if strategy == "id":
                                # Try direct ID first with explicit wait
                                element = extended_wait.until(EC.presence_of_element_located((By.ID, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("26/01/2026")
                                course_from_filled = True
                                log_operation("Course From date", "SUCCESS", f"Filled using ID: {selector}")
                                break
                            elif strategy == "xpath":
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("26/01/2026")
                                course_from_filled = True
                                log_operation("Course From date", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                            else:  # label
                                fill_date_by_label(browser, wait, selector, "", "26/01/2026")
                                course_from_filled = True
                                log_operation("Course From date", "SUCCESS", f"Filled using label: {selector}")
                                break
                        except Exception as e:
                            log_operation("Course From date", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not course_from_filled:
                        log_operation("Course From date", "WARN", "Could not fill Course From date using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Fill Course To date - try multiple strategies
                    course_to_filled = False
                    course_to_selectors = [
                        ("id", "ctl00_ContentPlaceHolder1_txtCourseDurationTill"),
                        ("xpath", "//input[contains(@id, 'CourseDurationTill') or contains(@name, 'CourseDurationTill')]"),
                        ("xpath", "//input[contains(@id, 'Course') and contains(@id, 'Duration') and contains(@id, 'Till')]"),
                        ("label", "To"),
                    ]
                    for strategy, selector in course_to_selectors:
                        try:
                            if strategy == "id":
                                fill_field_by_id(selector, "17/07/2026", "text")
                                course_to_filled = True
                                log_operation("Course To date", "SUCCESS", f"Filled using ID: {selector}")
                                break
                            elif strategy == "xpath":
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("17/07/2026")
                                course_to_filled = True
                                log_operation("Course To date", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                            else:  # label
                                fill_date_by_label(browser, wait, selector, "", "17/07/2026")
                                course_to_filled = True
                                log_operation("Course To date", "SUCCESS", f"Filled using label: {selector}")
                                break
                        except Exception as e:
                            log_operation("Course To date", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not course_to_filled:
                        log_operation("Course To date", "WARN", "Could not fill Course To date using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Fill Course fees paid
                    try:
                        select_radio_by_label(browser, wait, "Have you paid your course fees in full", "Yes")
                        time.sleep(OPERATION_DELAY)
                    except Exception as e:
                        log_operation("Course fees paid", "WARN", f"Error filling by label: {e}")
                        # Try direct ID (Yes = value 1, typically index 0)
                        try:
                            fill_field_by_id("ctl00_ContentPlaceHolder1_rdblstFeesPaid_0", "Yes", "radio", check_filled=False)
                            time.sleep(OPERATION_DELAY)
                        except:
                            pass
                    
                    # Fill Hours of organized daytime tuition per week
                    try:
                        fill_text_by_label(browser, wait, "Hours of organized daytime tuition per week", "18.25 hours")
                        time.sleep(OPERATION_DELAY)
                    except Exception as e:
                        log_operation("Hours per week", "WARN", f"Error filling by label: {e}")
                        # Try direct ID
                        try:
                            fill_field_by_id("ctl00_ContentPlaceHolder1_txtTuitionHours", "18.25 hours", "text")
                            time.sleep(OPERATION_DELAY)
                        except:
                            pass
                    
                    log_operation("Course fields", "SUCCESS", "Filled conditional course fields")
                else:
                    log_operation("Course fields", "INFO", "No course-related fields found (may not be required or not yet visible)")
            except Exception as e:
                log_operation("Course fields", "WARN", f"Error checking for conditional course fields: {e}")
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("Accepted on course", "WARN", f"Error: {e}")
        
        # 2. Have you studied in Ireland before? * (MANDATORY)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("Studied in Ireland before", "INFO", "Selecting studied in Ireland before (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_rdblstStudiedBefore_1", "No", "radio", check_filled=False)
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("Studied in Ireland before", "WARN", f"Error: {e}")
        
        # 3. Do you speak English? * (MANDATORY)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("Speak English", "INFO", "Selecting speak English (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_rdblstSpeakEnglish_0", "Yes", "radio", check_filled=False)
            # Wait for PostBack to complete (this may show/hide conditional fields)
            time.sleep(OPERATION_DELAY * 3)  # Wait longer for PostBack
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            # After selecting "Yes", check if conditional mandatory fields appear (e.g., Test Taken)
            log_operation("Speak English", "INFO", "Checking for conditional mandatory fields after selecting 'Yes'...")
            time.sleep(2)  # Wait for PostBack to complete and dynamic content to load
            
            # Check page source for Test Taken related labels/text
            try:
                page_source = browser.page_source
                has_test_taken = "Test Taken" in page_source or "test taken" in page_source.lower()
                has_overall_result = "Overall Result" in page_source or "overall result" in page_source.lower()
                
                if has_test_taken or has_overall_result:
                    log_operation("Test Taken fields", "INFO", "Found Test Taken related text in page, attempting to fill fields...")
                    
                    # Method 1: Try direct ID first, then label-based
                    test_taken_filled = False
                    test_taken_selectors = [
                        ("id", "ctl00_ContentPlaceHolder1_txtTestTaken1"),
                        ("xpath", "//input[@id='ctl00_ContentPlaceHolder1_txtTestTaken1']"),
                        ("xpath", "//input[contains(@id, 'TestTaken') or contains(@name, 'TestTaken')]"),
                        ("xpath", "//input[contains(@id, 'Test') and contains(@id, 'Taken')]"),
                        ("label", "Test Taken"),
                    ]
                    for strategy, selector in test_taken_selectors:
                        try:
                            if strategy == "id":
                                element = extended_wait.until(EC.presence_of_element_located((By.ID, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("IELTS Academic")
                                test_taken_filled = True
                                log_operation("Test Taken", "SUCCESS", f"Filled using ID: {selector}")
                                break
                            elif strategy == "xpath":
                                element = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.3)
                                element.clear()
                                time.sleep(0.2)
                                element.send_keys("IELTS Academic")
                                test_taken_filled = True
                                log_operation("Test Taken", "SUCCESS", f"Filled using XPath: {selector}")
                                break
                            else:  # label
                                fill_text_by_label(browser, wait, selector, "IELTS Academic")
                                test_taken_filled = True
                                log_operation("Test Taken", "SUCCESS", f"Filled using label: {selector}")
                                break
                        except Exception as e:
                            log_operation("Test Taken", "DEBUG", f"Strategy {strategy} failed: {e}")
                            continue
                    if not test_taken_filled:
                        log_operation("Test Taken", "WARN", "Could not fill Test Taken using any strategy")
                    time.sleep(OPERATION_DELAY)
                    
                    # Method 2: Fill Test Date (already has direct ID logic, keep it)
                    try:
                        
                        # Fill first Test Date - use direct ID first (most reliable)
                        try:
                            # Try direct ID for Test Taken Date 1
                            fill_field_by_id("ctl00_ContentPlaceHolder1_txtTestTakenDate1", "15/09/2024", "text")
                            time.sleep(OPERATION_DELAY)
                            log_operation("Test Taken Date", "SUCCESS", "Filled Test Taken Date using direct ID")
                        except:
                            # Fallback: Try to find by label "Date" near "Test Taken"
                            try:
                                fill_date_by_label(browser, wait, "Date", "", "15/09/2024")
                                time.sleep(OPERATION_DELAY)
                            except:
                                # Try finding date input near Test Taken label
                                try:
                                    test_taken_labels = browser.find_elements(By.XPATH, "//td[contains(text(), 'Test Taken') or contains(text(), 'test taken')]")
                                    if test_taken_labels:
                                        # Find input in same row or nearby
                                        for label in test_taken_labels:
                                            try:
                                                row = label.find_element(By.XPATH, "./ancestor::tr")
                                                date_inputs = row.find_elements(By.XPATH, ".//input[contains(@id, 'TestTakenDate') or contains(@name, 'TestTakenDate')]")
                                                if date_inputs:
                                                    date_input = date_inputs[0]
                                                    date_id = date_input.get_attribute("id")
                                                    if date_id:
                                                        fill_field_by_id(date_id, "15/09/2024", "text")
                                                        time.sleep(OPERATION_DELAY)
                                                        break
                                            except:
                                                continue
                                except:
                                    log_operation("Test Taken Date", "WARN", "Could not fill Test Taken Date")
                        
                        # Fill first Overall Result
                        fill_text_by_label(browser, wait, "Overall Result Achieved", "5.5")
                        time.sleep(OPERATION_DELAY)
                        
                        log_operation("Test Taken fields", "SUCCESS", "Filled conditional Test Taken fields")
                    except Exception as e:
                        log_operation("Test Taken fields", "WARN", f"Error filling Test Taken fields by label: {e}")
                        
                        # Method 2: Fallback - try to find by ID patterns
                        try:
                            test_taken_inputs = browser.find_elements(By.XPATH, "//input[contains(@id, 'TestTaken') or contains(@name, 'TestTaken') or contains(@id, 'Test')]")
                            test_date_inputs = browser.find_elements(By.XPATH, "//input[contains(@id, 'Date') and (contains(@id, 'Test') or contains(@name, 'Test'))]")
                            result_inputs = browser.find_elements(By.XPATH, "//input[contains(@id, 'OverallResult') or contains(@id, 'Result')]")
                            
                            if test_taken_inputs:
                                test_input = test_taken_inputs[0]
                                test_id = test_input.get_attribute("id")
                                if test_id:
                                    fill_field_by_id(test_id, "IELTS Academic", "text")
                                    time.sleep(OPERATION_DELAY)
                            
                            if test_date_inputs:
                                date_input = test_date_inputs[0]
                                date_id = date_input.get_attribute("id")
                                if date_id:
                                    fill_field_by_id(date_id, "15/09/2024", "text")
                                    time.sleep(OPERATION_DELAY)
                            
                            if result_inputs:
                                result_input = result_inputs[0]
                                result_id = result_input.get_attribute("id")
                                if result_id:
                                    fill_field_by_id(result_id, "5.5", "text")
                                    time.sleep(OPERATION_DELAY)
                        except Exception as e2:
                            log_operation("Test Taken fields", "WARN", f"Error filling Test Taken fields by ID: {e2}")
                else:
                    log_operation("Test Taken fields", "INFO", "No Test Taken related text found in page (may not be required or not yet visible)")
            except Exception as e:
                log_operation("Test Taken fields", "WARN", f"Error checking for conditional Test Taken fields: {e}")
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("Speak English", "WARN", f"Error: {e}")
        
        # 4. Name of School/College * (MANDATORY - First educational qualification)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("First School/College", "INFO", "Filling first School/College (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_txtSchoolColl1", "Hangzhou No.2 High School", "textarea")
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("First School/College", "WARN", f"Error: {e}")
        
        # 5. Date From * (MANDATORY - First educational qualification)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("First Education From Date", "INFO", "Filling first education From date (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_txtEduFrom1", "01/09/2020", "text")
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("First Education From Date", "WARN", f"Error: {e}")
        
        # 6. Date To * (MANDATORY - First educational qualification)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("First Education To Date", "INFO", "Filling first education To date (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_txtEduTill1", "30/06/2023", "text")
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("First Education To Date", "WARN", f"Error: {e}")
        
        # 7. Qualification Obtained * (MANDATORY - First educational qualification)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("First Qualification", "INFO", "Filling first qualification (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_txtQualObtained1", "High School Diploma", "text")
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("First Qualification", "WARN", f"Error: {e}")
        
        # 8. How will your studies be supported financially? * (MANDATORY)
        try:
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
            
            log_operation("Financial Support", "INFO", "Selecting financial support (MANDATORY)...")
            fill_field_by_id("ctl00_ContentPlaceHolder1_rdblstSponsor_0", "Self", "radio", check_filled=False)
            time.sleep(OPERATION_DELAY)
            
            redirect_check = check_homepage_redirect(browser, wait)
            if redirect_check == "homepage":
                return "homepage_redirect"
        except Exception as e:
            log_operation("Financial Support", "WARN", f"Error: {e}")
        
        
        # Check for homepage redirect after filling all fields
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Detected redirect to homepage after filling all fields, stopping...")
            page_state = detect_current_page_state(browser, wait)
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        
        log_operation("fill_page_9", "SUCCESS", "Page 9 filled successfully")
        
        # Final verification before proceeding
        current_url = browser.current_url
        log_operation("fill_page_9", "INFO", f"Current URL after filling Page 9: {current_url}")
        
        # CRITICAL: Check for homepage redirect BEFORE attempting to click button
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Detected redirect to homepage after filling fields, stopping before clicking button...")
            page_state = detect_current_page_state(browser, wait)
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        
        # Check for error page
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_page_9", "WARN", "Error page redirected to homepage, stopping...")
            page_state = detect_current_page_state(browser, wait)
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        
        # Check again after error page check (error page handling might cause redirect)
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Detected redirect to homepage after error page check, stopping before clicking button...")
            page_state = detect_current_page_state(browser, wait)
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        
        # Verify page state before clicking button
        log_operation("fill_page_9", "INFO", "Verifying page state before clicking 'Save and Continue' button...")
        try:
            # Check if page is ready
            ready_state = browser.execute_script("return document.readyState")
            if ready_state == "complete":
                log_operation("fill_page_9", "INFO", "Page state verified, proceeding to click 'Save and Continue' button...")
            else:
                log_operation("fill_page_9", "WARN", "Page state verification failed, but proceeding to click button...")
        except Exception as e:
            log_operation("fill_page_9", "WARN", f"Error verifying page state: {e}, but proceeding...")
        
        # Check again for homepage redirect after verification
        redirect_check = check_homepage_redirect(browser, wait)
        if redirect_check == "homepage":
            log_operation("fill_page_9", "WARN", "Detected redirect to homepage during verification, stopping before clicking button...")
            page_state = detect_current_page_state(browser, wait)
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        
        # Click Next/Continue button to go to next page
        button_result = click_next_button(browser, wait)
        
        # Check if button click resulted in homepage redirect
        if button_result == "homepage":
            log_operation("fill_page_9", "WARN", "Button click redirected to homepage, detecting page state...")
            page_state = detect_current_page_state(browser, wait)
            
            if page_state['page_type'] == 'homepage':
                log_operation("fill_page_9", "INFO", "Confirmed on homepage, will restart from homepage in fill_application_form")
                return "homepage_redirect"
            elif page_state['page_type'] == 'form_page':
                log_operation("fill_page_9", "INFO", f"Back on form page {page_state['page_number']}, will continue from there")
                return f"form_page_{page_state['page_number']}"
        elif button_result == "same_page":
            log_operation("fill_page_9", "WARN", "Still on same page after clicking button - may be validation error or page jump")
            # Refresh page to get latest state
            log_operation("fill_page_9", "INFO", "Refreshing page to detect current page state...")
            browser.refresh()
            time.sleep(3)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)
            
            # Check for validation errors on the page
            try:
                error_elements = browser.find_elements(By.CLASS_NAME, "error")
                if error_elements:
                    error_texts = [elem.text for elem in error_elements if elem.text]
                    log_operation("fill_page_9", "WARN", f"Found validation errors: {error_texts}")
            except:
                pass
            
            # Detect current page number
            page_number = detect_page_number_no_refresh(browser, wait)
            if page_number:
                log_operation("fill_page_9", "INFO", f"After refresh, detected page {page_number}, returning form_page_{page_number}")
                return f"form_page_{page_number}"
            else:
                log_operation("fill_page_9", "WARN", "After refresh, could not detect page number, returning same_page")
                return "same_page"
        
        # After clicking Next button, check for Application Number
        # Application Number may appear after submitting page 3 or later
        time.sleep(2)  # Wait for page to load after navigation
        application_number = extract_application_number(browser, wait)
        if application_number:
            log_operation("fill_page_9", "SUCCESS", f"Application Number detected after Page 9: {application_number}")
            # Save Application Number to a file for future use (with validation)
            save_application_number(application_number)
        
        # Return success to indicate successful completion (if no redirect)
        return True
        
    except Exception as e:
        log_operation("fill_page_9", "ERROR", f"Error filling Page 9: {e}")
        import traceback
        traceback.print_exc()
        # Check if we're on homepage (which means we should restart)
        try:
            current_url = browser.current_url
            if "OnlineHome.aspx" in current_url:
                log_operation("fill_page_9", "WARN", "On homepage after error - returning homepage_redirect to trigger restart")
                return "homepage_redirect"
        except:
            pass
        return "error"




