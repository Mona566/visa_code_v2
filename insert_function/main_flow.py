from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# 导入所有需要的函数
from .utils import (
    OPERATION_DELAY, POSTBACK_DELAY, POSTBACK_WAIT_DELAY, POSTBACK_BETWEEN_DELAY,
    log_operation, take_screenshot
)
from .page_detection import (
    check_and_handle_error_page, handle_intermediate_page,
    restart_from_homepage, detect_current_page_state
)
from .application_management import (
    get_saved_application_number, retrieve_application, extract_application_number
)
from .page_fillers import (
    fill_page_1, fill_page_2, fill_page_3, fill_page_4, fill_page_5,
    fill_page_6, fill_page_7, fill_page_8, fill_page_9, fill_page_10
)

def initialize_form_session(browser, wait):
    """
    Navigate through the INIS homepage and privacy statement to reach the form entry page.

    This must be called before fill_page_1(). It handles:
      1. OnlineHome.aspx  → click "Continue"
      2. OnlineHome2.aspx → check privacy checkbox + click submit
      3. Wait for VisaTypeDetails.aspx

    Args:
        browser: Selenium WebDriver instance (already open)
        wait:    WebDriverWait instance

    Returns:
        bool: True if the browser is now on VisaTypeDetails.aspx, False otherwise.
    """
    homepage_url = "https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx"

    try:
        # Navigate to homepage if not already there
        current_url = browser.current_url
        if "OnlineHome.aspx" not in current_url:
            log_operation("initialize_form_session", "INFO", f"Navigating to homepage: {homepage_url}")
            browser.get(homepage_url)
            time.sleep(3)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        # ── Step 1: Click "Continue" on OnlineHome.aspx ──────────────────────
        log_operation("initialize_form_session", "INFO", "Looking for Continue button...")
        continue_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
            (By.XPATH, "//input[@type='submit' and @value='Continue']"),
            (By.XPATH, "//input[@type='button' and @value='Continue']"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
            (By.XPATH, "//a[contains(text(), 'Continue')]"),
            (By.CSS_SELECTOR, "input[value='Continue']"),
        ]
        continue_button = None
        for by, selector in continue_selectors:
            try:
                continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("initialize_form_session", "SUCCESS", f"Found Continue button: {by}={selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not continue_button:
            log_operation("initialize_form_session", "ERROR", "Continue button not found on homepage")
            return False

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
        time.sleep(0.5)
        try:
            continue_button.click()
        except Exception:
            browser.execute_script("arguments[0].click();", continue_button)
        log_operation("initialize_form_session", "INFO", "Clicked Continue, waiting for OnlineHome2.aspx...")

        # Wait for intermediate page (OnlineHome2.aspx)
        try:
            wait.until(lambda d: "OnlineHome2.aspx" in d.current_url or "VisaTypeDetails.aspx" in d.current_url)
        except TimeoutException:
            pass
        time.sleep(2)

        # If already on form page, we're done
        if "VisaTypeDetails.aspx" in browser.current_url:
            log_operation("initialize_form_session", "SUCCESS", "Reached form page directly")
            return True

        # ── Step 2: Privacy checkbox + submit on OnlineHome2.aspx ────────────
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        log_operation("initialize_form_session", "INFO", "On OnlineHome2.aspx — looking for privacy checkbox...")

        privacy_checkbox = None
        privacy_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_CheckBoxRead"),
            (By.XPATH, "//input[@type='checkbox' and contains(@id, 'CheckBoxRead')]"),
            (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//preceding::input[@type='checkbox'][1]"),
            (By.XPATH, "//label[contains(text(), 'I acknowledge')]//following::input[@type='checkbox'][1]"),
        ]
        for by, selector in privacy_selectors:
            try:
                privacy_checkbox = browser.find_element(by, selector)
                if privacy_checkbox.is_displayed():
                    log_operation("initialize_form_session", "SUCCESS", f"Found privacy checkbox: {by}={selector}")
                    break
            except NoSuchElementException:
                continue

        if privacy_checkbox:
            browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", privacy_checkbox)
            time.sleep(0.5)
            if not privacy_checkbox.is_selected():
                privacy_checkbox.click()
                log_operation("initialize_form_session", "SUCCESS", "Privacy checkbox checked")
            else:
                log_operation("initialize_form_session", "INFO", "Privacy checkbox already checked")
            time.sleep(1)
        else:
            log_operation("initialize_form_session", "WARN", "Privacy checkbox not found — continuing anyway")

        # Find and click the submit button (use a short 3s wait per selector to fail fast)
        short_wait = WebDriverWait(browser, 3)
        submit_selectors = [
            (By.ID, "ctl00_ContentPlaceHolder1_btnSave"),
            (By.ID, "ctl00_ContentPlaceHolder1_btnContinue"),
            (By.ID, "ctl00_MainContent_btnContinue"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'Continue')]"),
            (By.XPATH, "//input[@type='submit' and contains(@value, 'Save and Continue')]"),
            (By.XPATH, "//input[@type='button' and contains(@value, 'Continue')]"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
        ]
        submit_button = None
        for by, selector in submit_selectors:
            try:
                submit_button = short_wait.until(EC.element_to_be_clickable((by, selector)))
                log_operation("initialize_form_session", "SUCCESS", f"Found submit button: {by}={selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not submit_button:
            log_operation("initialize_form_session", "ERROR", "Submit button not found on privacy page")
            return False

        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        time.sleep(0.5)
        try:
            submit_button.click()
        except Exception:
            browser.execute_script("arguments[0].click();", submit_button)
        log_operation("initialize_form_session", "INFO", "Clicked submit, waiting for form page...")

        # Wait for form page
        try:
            wait.until(lambda d: "VisaTypeDetails.aspx" in d.current_url)
        except TimeoutException:
            pass
        time.sleep(2)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

        if "VisaTypeDetails.aspx" in browser.current_url:
            log_operation("initialize_form_session", "SUCCESS", f"Session initialized — on form page: {browser.current_url}")
            return True

        log_operation("initialize_form_session", "ERROR", f"Unexpected URL after initialization: {browser.current_url}")
        return False

    except Exception as e:
        log_operation("initialize_form_session", "ERROR", f"Exception during initialization: {str(e)[:300]}")
        return False


def auto_fill_inis_form():
    """
    Automatically open the Irish visa application webpage, click continue and agree buttons,
    and enter the application form page
    """
    # Keep the browser window open
    options = Options()
    options.add_experimental_option("detach", True)
    
    # Set browser window size - maximize for better visibility
    options.add_argument("--start-maximized")
    
    # Ensure browser is visible (not headless)
    # options.add_argument("--headless")  # Uncomment this line if you want to run in background

    # Start browser
    browser = webdriver.Chrome(options=options)
    wait = WebDriverWait(browser, 10)  # Wait up to 10 seconds

    try:
        # Visit target page
        target_url = "https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx"
        print(f"[INFO] Opening webpage: {target_url}")
        browser.get(target_url)
        
        # Wait for page to load
        time.sleep(3)
        print(f"[INFO] Page title: {browser.title}")
        
        # Check for error page
        check_and_handle_error_page(browser, wait)

        # IMPORTANT: Always check for saved Application Number first, regardless of current page
        # This ensures we can retrieve application even if we're not on homepage
        saved_app_number = get_saved_application_number()
        current_url = browser.current_url
        
        if saved_app_number:
            log_operation("auto_fill_inis_form", "INFO", f"Found saved Application Number: {saved_app_number}, checking if we need to retrieve application...")
            
            # If we're on homepage, retrieve application
            if "OnlineHome.aspx" in current_url:
                log_operation("auto_fill_inis_form", "INFO", f"On homepage, attempting to retrieve application with Application Number: {saved_app_number}")
                app_number_to_use = saved_app_number
                
                # Call retrieve_application function
                if retrieve_application(browser, wait, app_number_to_use):
                    log_operation("auto_fill_inis_form", "SUCCESS", "Successfully retrieved application, continuing with form filling...")
                    # After retrieving, wait for page to load and continue
                    time.sleep(3)
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    time.sleep(2)
                    # Check if we're now on form page
                    new_url = browser.current_url
                    if "VisaTypeDetails.aspx" in new_url or "StudentVisa.aspx" in new_url or "GeneralApplicantInfo.aspx" in new_url:
                        log_operation("auto_fill_inis_form", "SUCCESS", "After retrieving application, on form page - proceeding to fill form")
                        # Continue to fill application form
                        fill_application_form(browser, wait)
                        return
                    elif "OnlineHome.aspx" in new_url:
                        log_operation("auto_fill_inis_form", "WARN", f"After retrieving application, redirected back to homepage: {new_url}")
                        # Re-retrieve application if we have application number
                        if saved_app_number:
                            log_operation("auto_fill_inis_form", "INFO", f"Re-retrieving application with Application Number: {saved_app_number}")
                            if retrieve_application(browser, wait, saved_app_number):
                                log_operation("auto_fill_inis_form", "SUCCESS", "Successfully re-retrieved application")
                                # Check URL again
                                final_url = browser.current_url
                                if "VisaTypeDetails.aspx" in final_url or "StudentVisa.aspx" in final_url or "GeneralApplicantInfo.aspx" in final_url:
                                    fill_application_form(browser, wait)
                                    return
                        log_operation("auto_fill_inis_form", "INFO", f"After retrieving application, on page: {new_url}, continuing...")
                    else:
                        log_operation("auto_fill_inis_form", "INFO", f"After retrieving application, on page: {new_url}, continuing...")
                else:
                    log_operation("auto_fill_inis_form", "WARN", "Failed to retrieve application, will try Continue button instead")
            # If we're already on form page but have saved Application Number, 
            # we should still try to retrieve to ensure we're on the correct application
            elif "VisaTypeDetails.aspx" in current_url:
                log_operation("auto_fill_inis_form", "INFO", f"Already on form page, but have saved Application Number: {saved_app_number}")
                log_operation("auto_fill_inis_form", "INFO", "Navigating to homepage to retrieve application...")
                # Navigate to homepage first
                try:
                    browser.get("https://www.visas.inis.gov.ie/AVATS/OnlineHome.aspx")
                    time.sleep(3)
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    time.sleep(2)
                    
                    # Now retrieve application
                    if retrieve_application(browser, wait, saved_app_number):
                        log_operation("auto_fill_inis_form", "SUCCESS", "Successfully retrieved application from homepage")
                        time.sleep(3)
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        time.sleep(2)
                        # Continue to fill application form
                        fill_application_form(browser, wait)
                        return
                    else:
                        log_operation("auto_fill_inis_form", "WARN", "Failed to retrieve application, proceeding with current form page")
                except Exception as e:
                    log_operation("auto_fill_inis_form", "WARN", f"Error navigating to homepage for retrieval: {e}, proceeding with current form page")
        else:
            # No saved Application Number found
            log_operation("auto_fill_inis_form", "INFO", "No saved Application Number found")
        
        # Check if we're already on form page (after retrieve or direct navigation)
        current_url_check = browser.current_url
        if "VisaTypeDetails.aspx" in current_url_check:
            log_operation("auto_fill_inis_form", "INFO", "Already on form page, proceeding to fill form")
            fill_application_form(browser, wait)
            return
        
        # ------------------------------------------------
        # Step 1: Find and click "Continue" button (only if no Application Number found or not on form page)
        # ------------------------------------------------
        print("[INFO] Looking for 'Continue' button...")
        continue_button = None
        
        # Try multiple ways to find the "Continue" button
        continue_selectors = [
            (By.ID, "ctl00_MainContent_btnContinue"),  # Possible ID
            (By.ID, "btnContinue"),
            (By.XPATH, "//input[@type='submit' and @value='Continue']"),
            (By.XPATH, "//button[contains(text(), 'Continue')]"),
            (By.XPATH, "//a[contains(text(), 'Continue')]"),
            (By.CSS_SELECTOR, "input[value*='Continue']"),
        ]
        
        for by, selector in continue_selectors:
            try:
                continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                print(f"[SUCCESS] Found 'Continue' button: {by}={selector}")
                break
            except (TimeoutException, NoSuchElementException):
                continue
        
        if continue_button:
            # Store current URL before clicking
            current_url = browser.current_url
            print(f"[INFO] Current URL before click: {current_url}")
            
            # Check if button is enabled and visible
            try:
                is_enabled = continue_button.is_enabled()
                is_displayed = continue_button.is_displayed()
                print(f"[DEBUG] Button enabled: {is_enabled}, displayed: {is_displayed}")
                if not is_enabled:
                    print("[WARN] Button is not enabled, waiting for it to become enabled...")
                    wait.until(EC.element_to_be_clickable(continue_button))
            except Exception as e:
                print(f"[WARN] Could not check button state: {e}")
            
            # Scroll to button to ensure it's visible
            browser.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", continue_button)
            time.sleep(1)  # Wait for scroll animation
            
            # Check for any error messages or validation issues before clicking
            try:
                error_messages = browser.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'validation') or contains(@id, 'error')]")
                if error_messages:
                    print(f"[WARN] Found {len(error_messages)} potential error/validation elements")
                    for err in error_messages[:3]:  # Show first 3
                        try:
                            if err.is_displayed() and err.text.strip():
                                print(f"[WARN] Error message: {err.text.strip()[:100]}")
                        except:
                            pass
            except:
                pass
            
            # Wait for any pending JavaScript/AJAX to complete
            try:
                browser.execute_script("return jQuery.active == 0")  # Check if jQuery is active
                print("[DEBUG] Checking for pending AJAX requests...")
            except:
                pass  # jQuery might not be available
            
            time.sleep(1)  # Additional wait before clicking
            
            # Try multiple click methods to ensure click is registered
            click_success = False
            try:
                # Method 1: Standard click
                continue_button.click()
                print("[SUCCESS] Clicked 'Continue' button (standard click)")
                click_success = True
            except Exception as e1:
                print(f"[WARN] Standard click failed: {e1}, trying JavaScript click...")
                try:
                    # Method 2: JavaScript click
                    browser.execute_script("arguments[0].click();", continue_button)
                    print("[SUCCESS] Clicked 'Continue' button (JavaScript click)")
                    click_success = True
                except Exception as e2:
                    print(f"[WARN] JavaScript click failed: {e2}, trying ActionChains...")
                    try:
                        # Method 3: ActionChains click
                        ActionChains(browser).move_to_element(continue_button).click().perform()
                        print("[SUCCESS] Clicked 'Continue' button (ActionChains click)")
                        click_success = True
                    except Exception as e3:
                        print(f"[ERROR] All click methods failed. Last error: {e3}")
                        # Try direct JavaScript event trigger
                        try:
                            browser.execute_script("""
                                var btn = arguments[0];
                                var event = new MouseEvent('click', {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true
                                });
                                btn.dispatchEvent(event);
                            """, continue_button)
                            print("[SUCCESS] Clicked 'Continue' button (event dispatch)")
                            click_success = True
                        except Exception as e4:
                            print(f"[ERROR] Event dispatch also failed: {e4}")
            
            if not click_success:
                print("[ERROR] Failed to click Continue button with all methods")
                return
            
            # Wait for page to navigate - check for URL change or document ready
            max_wait = 20  # Increased wait time
            start_time = time.time()
            navigated = False
            
            print("[INFO] Waiting for page navigation...")
            while time.time() - start_time < max_wait:
                try:
                    # Check if URL changed
                    new_url = browser.current_url
                    if new_url != current_url:
                        print(f"[SUCCESS] URL changed from {current_url} to {new_url}")
                        navigated = True
                        break
                    
                    # Check if page is ready (document.readyState)
                    ready_state = browser.execute_script("return document.readyState")
                    
                    # Check for loading indicators
                    try:
                        loading_indicators = browser.find_elements(By.XPATH, "//*[contains(@class, 'loading') or contains(@id, 'loading')]")
                        if loading_indicators:
                            is_loading = any(ind.is_displayed() for ind in loading_indicators)
                            if is_loading:
                                print("[DEBUG] Page is still loading...")
                    except:
                        pass
                    
                    # Check if we can find elements that indicate new page loaded
                    if ready_state == "complete":
                        checkboxes = browser.find_elements(By.XPATH, "//input[@type='checkbox']")
                        if len(checkboxes) > 0 and len(checkboxes) != len(browser.find_elements(By.XPATH, "//input[@type='checkbox']")):
                            print(f"[INFO] Found {len(checkboxes)} checkboxes, page may have loaded")
                            # Double check URL hasn't changed
                            if browser.current_url != current_url:
                                navigated = True
                                break
                    
                    elapsed = time.time() - start_time
                    if elapsed % 3 < 0.5:  # Print every 3 seconds
                        print(f"[DEBUG] Still waiting... ({int(elapsed)}s elapsed, URL: {new_url})")
                    
                    time.sleep(0.5)  # Check every 0.5 seconds
                except Exception as e:
                    print(f"[DEBUG] Check error: {e}")
                    time.sleep(0.5)
            
            if not navigated:
                print(f"[WARN] Page navigation not detected after {max_wait} seconds")
                print(f"[INFO] Current URL: {browser.current_url}")
                
                # If still on homepage, try clicking Continue button again
                current_url_after_wait = browser.current_url
                if "OnlineHome.aspx" in current_url_after_wait:
                    print("[INFO] Still on homepage after waiting, will retry clicking Continue button...")
                    
                    # Try to find and click Continue button again
                    max_retries = 3
                    for retry_count in range(1, max_retries + 1):
                        try:
                            print(f"[INFO] Retry attempt {retry_count}/{max_retries}: Looking for Continue button...")
                            time.sleep(2)  # Wait a bit before retrying
                            
                            # Wait for page to be ready
                            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                            
                            # Find Continue button again
                            continue_button_selectors = [
                                (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
                                (By.XPATH, "//input[@type='submit' and @value='Continue']"),
                                (By.XPATH, "//input[@type='button' and @value='Continue']"),
                                (By.XPATH, "//button[contains(text(), 'Continue')]"),
                                (By.XPATH, "//a[contains(text(), 'Continue')]"),
                                (By.CSS_SELECTOR, "input[value='Continue']"),
                            ]
                            
                            continue_button_retry = None
                            for by, selector in continue_button_selectors:
                                try:
                                    continue_button_retry = browser.find_element(by, selector)
                                    if continue_button_retry.is_displayed() and continue_button_retry.is_enabled():
                                        print(f"[SUCCESS] Found Continue button for retry: {by}={selector}")
                                        break
                                except:
                                    continue
                            
                            if continue_button_retry:
                                # Scroll to button
                                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button_retry)
                                time.sleep(1)
                                
                                # Try to click
                                try:
                                    continue_button_retry.click()
                                    print(f"[SUCCESS] Clicked Continue button (retry {retry_count})")
                                except:
                                    try:
                                        browser.execute_script("arguments[0].click();", continue_button_retry)
                                        print(f"[SUCCESS] Clicked Continue button using JavaScript (retry {retry_count})")
                                    except:
                                        ActionChains(browser).move_to_element(continue_button_retry).click().perform()
                                        print(f"[SUCCESS] Clicked Continue button using ActionChains (retry {retry_count})")
                                
                                # Wait for navigation after retry click
                                print("[INFO] Waiting for page navigation after retry click...")
                                retry_wait_time = 15
                                retry_start_time = time.time()
                                retry_navigated = False
                                
                                while time.time() - retry_start_time < retry_wait_time:
                                    try:
                                        retry_url = browser.current_url
                                        if retry_url != current_url_after_wait:
                                            print(f"[SUCCESS] URL changed after retry: {retry_url}")
                                            retry_navigated = True
                                            navigated = True  # Update main navigation flag
                                            break
                                        
                                        # Check if we're on form page
                                        if "VisaTypeDetails.aspx" in retry_url or "OnlineHome2.aspx" in retry_url:
                                            print(f"[SUCCESS] Navigated to form/intermediate page after retry: {retry_url}")
                                            retry_navigated = True
                                            navigated = True
                                            break
                                        
                                        time.sleep(0.5)
                                    except:
                                        time.sleep(0.5)
                                
                                if retry_navigated:
                                    print("[SUCCESS] Page navigation successful after retry!")
                                    break
                                else:
                                    print(f"[WARN] Retry {retry_count} did not result in navigation")
                            else:
                                print(f"[WARN] Continue button not found for retry {retry_count}")
                                
                        except Exception as retry_error:
                            print(f"[WARN] Error during retry {retry_count}: {retry_error}")
                            continue
                    
                    # If all retries failed, check page state
                    if not navigated:
                        print("[WARN] All retry attempts failed, checking page state...")
                        print(f"[INFO] Current URL: {browser.current_url}")
                        
                        # Check if page title changed
                        try:
                            new_title = browser.title
                            print(f"[INFO] Page title: {new_title}")
                        except:
                            pass
                        
                        # Check for any error messages
                        try:
                            alerts = browser.find_elements(By.XPATH, "//*[contains(@class, 'alert') or contains(@class, 'message')]")
                            for alert in alerts[:3]:
                                if alert.is_displayed() and alert.text.strip():
                                    print(f"[INFO] Page message: {alert.text.strip()[:200]}")
                        except:
                            pass
                else:
                    # Not on homepage, just check page content
                    print("[INFO] Checking if page content changed...")
                    
                    # Check if page title changed
                    try:
                        new_title = browser.title
                        print(f"[INFO] Page title: {new_title}")
                    except:
                        pass
                    
                    # Check for any error messages
                    try:
                        alerts = browser.find_elements(By.XPATH, "//*[contains(@class, 'alert') or contains(@class, 'message')]")
                        for alert in alerts[:3]:
                            if alert.is_displayed() and alert.text.strip():
                                print(f"[INFO] Page message: {alert.text.strip()[:200]}")
                    except:
                        pass
            else:
                print("[SUCCESS] Page navigation confirmed")
            
            # Additional wait to ensure page is fully loaded
            print("[INFO] Waiting for page to fully load...")
            time.sleep(3)
            
            # Final check
            print(f"[INFO] Final URL: {browser.current_url}")
            print(f"[INFO] Page title: {browser.title}")
        else:
            print("[WARN] 'Continue' button not found, trying to find other possible buttons...")
            
            # Try to find all possible buttons
            try:
                all_buttons = browser.find_elements(By.TAG_NAME, "input")
                print(f"[DEBUG] Found {len(all_buttons)} input elements on the page")
                for btn in all_buttons:
                    btn_type = btn.get_attribute("type")
                    btn_value = btn.get_attribute("value") or ""
                    if btn_type == "submit" and "continue" in btn_value.lower():
                        current_url = browser.current_url
                        btn.click()
                        print(f"[SUCCESS] Clicked button: {btn_value}")
                        # Wait for navigation
                        try:
                            wait.until(lambda driver: driver.current_url != current_url)
                            time.sleep(3)
                        except TimeoutException:
                            time.sleep(5)
                        break
            except Exception as e:
                print(f"[ERROR] Error finding button: {e}")

        # ------------------------------------------------
        # Step 2: Find and check the privacy statement checkbox
        # ------------------------------------------------
        print(f"[INFO] Current page before looking for checkbox: {browser.current_url}")
        print("[INFO] Looking for privacy statement checkbox...")
        privacy_checkbox = None
        
        # Key parts of privacy statement text
        privacy_text_keywords = [
            "I acknowledge that I have read and understood",
            "Privacy Notice",
            "fair and transparent processing",
            "personal data"
        ]
        
        # Wait a bit more to ensure page is fully loaded
        time.sleep(2)
        
        # Try multiple ways to find the privacy statement checkbox
        # Method 1: Find by label text (checkboxes usually have label tags)
        try:
            # Find label containing privacy statement text, then find associated checkbox
            privacy_label_xpath = "//label[contains(text(), 'I acknowledge that I have read and understood')]"
            privacy_label = wait.until(EC.presence_of_element_located((By.XPATH, privacy_label_xpath)))
            # Get label's for attribute to find corresponding checkbox
            label_for = privacy_label.get_attribute("for")
            if label_for:
                privacy_checkbox = browser.find_element(By.ID, label_for)
                print(f"[SUCCESS] Found privacy checkbox via label: ID={label_for}")
            else:
                # If label has no for attribute, find checkbox inside label
                privacy_checkbox = privacy_label.find_element(By.XPATH, ".//input[@type='checkbox']")
                print("[SUCCESS] Found privacy checkbox via checkbox inside label")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[INFO] Method 1 failed: {e}, trying other methods...")
            # Print page source snippet for debugging
            try:
                page_source = browser.page_source
                if "I acknowledge" in page_source:
                    print("[DEBUG] Privacy text found in page source, but element not found")
                else:
                    print("[DEBUG] Privacy text not found in page source")
            except:
                pass
        
        # Method 2: Find by text near checkbox
        if not privacy_checkbox:
            try:
                # Find all checkboxes, then check text near them
                all_checkboxes = browser.find_elements(By.XPATH, "//input[@type='checkbox']")
                for checkbox in all_checkboxes:
                    try:
                        # Get text from parent or sibling elements
                        parent = checkbox.find_element(By.XPATH, "./..")
                        parent_text = parent.text
                        # Check if it contains privacy statement keywords
                        if any(keyword.lower() in parent_text.lower() for keyword in privacy_text_keywords):
                            privacy_checkbox = checkbox
                            print("[SUCCESS] Found privacy checkbox via text matching")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"[INFO] Method 2 search error: {e}")
        
        # Method 3: Find via XPath directly for checkbox context containing specific text
        if not privacy_checkbox:
            try:
                privacy_checkbox_xpath = "//input[@type='checkbox'][contains(../text(), 'I acknowledge that I have read and understood') or contains(../label/text(), 'I acknowledge that I have read and understood')]"
                privacy_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, privacy_checkbox_xpath)))
                print("[SUCCESS] Found privacy checkbox via XPath")
            except (TimeoutException, NoSuchElementException):
                print("[INFO] Method 3 failed, trying generic method...")
        
        # Method 4: Generic method - find all unchecked checkboxes and check surrounding text
        if not privacy_checkbox:
            try:
                all_checkboxes = browser.find_elements(By.XPATH, "//input[@type='checkbox']")
                for checkbox in all_checkboxes:
                    if not checkbox.is_selected():
                        # Try to get text related to checkbox
                        try:
                            # Find checkbox's parent element
                            checkbox_id = checkbox.get_attribute("id")
                            if checkbox_id:
                                # Find corresponding label
                                label = browser.find_element(By.XPATH, f"//label[@for='{checkbox_id}']")
                                label_text = label.text
                                if "Privacy Notice" in label_text or "I acknowledge" in label_text:
                                    privacy_checkbox = checkbox
                                    print("[SUCCESS] Found privacy checkbox via label text")
                                    break
                        except:
                            # If label not found, check parent element text
                            try:
                                parent = checkbox.find_element(By.XPATH, "./..")
                                parent_text = parent.text
                                if "Privacy Notice" in parent_text or "I acknowledge" in parent_text:
                                    privacy_checkbox = checkbox
                                    print("[SUCCESS] Found privacy checkbox via parent element text")
                                    break
                            except:
                                continue
            except Exception as e:
                print(f"[INFO] Method 4 search error: {e}")
        
        # Check the checkbox
        if privacy_checkbox:
            try:
                # Scroll to make checkbox visible
                browser.execute_script("arguments[0].scrollIntoView(true);", privacy_checkbox)
                time.sleep(0.5)
                
                # If not selected, check it
                if not privacy_checkbox.is_selected():
                    privacy_checkbox.click()
                    print("[SUCCESS] Privacy checkbox checked")
                else:
                    print("[INFO] Privacy checkbox already checked")
                
                time.sleep(1)
                
                # Find and click submit/continue button
                print("[INFO] Looking for submit button...")
                submit_button = None
                submit_selectors = [
                    (By.XPATH, "//input[@type='submit']"),
                    (By.XPATH, "//input[@type='button' and (@value='Continue' or @value='Submit' or @value='Next')]"),
                    (By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Submit') or contains(text(), 'Next')]"),
                    (By.ID, "ctl00_MainContent_btnContinue"),
                    (By.ID, "btnContinue"),
                ]
                
                for by, selector in submit_selectors:
                    try:
                        submit_button = wait.until(EC.element_to_be_clickable((by, selector)))
                        print(f"[SUCCESS] Found submit button: {by}={selector}")
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                if submit_button:
                    # Record current URL before clicking
                    current_url = browser.current_url
                    print(f"[INFO] Current URL before clicking submit: {current_url}")
                    
                    submit_button.click()
                    print("[SUCCESS] Clicked submit button")
                    
                    # Wait for page navigation with proper detection
                    print("[INFO] Waiting for page navigation after clicking submit...")
                    max_wait = 20
                    start_time = time.time()
                    navigated = False
                    
                    while time.time() - start_time < max_wait:
                        try:
                            new_url = browser.current_url
                            ready_state = browser.execute_script("return document.readyState")
                            
                            # Check if URL changed
                            if new_url != current_url:
                                print(f"[INFO] URL changed to: {new_url}")
                                
                                # Check if we're on the form page or an intermediate page
                                if "VisaTypeDetails.aspx" in new_url:
                                    print("[SUCCESS] Navigated to form page (VisaTypeDetails.aspx)")
                                    navigated = True
                                    break
                                elif "OnlineHome2.aspx" in new_url:
                                    print("[INFO] On intermediate page (OnlineHome2.aspx), waiting for final navigation...")
                                    # This might be an intermediate page that redirects to the form
                                    # Wait indefinitely until redirect to form page or homepage
                                    intermediate_wait_count = 0
                                    intermediate_redirected = False
                                    retry_attempted = False  # Track if we've already retried
                                    while not intermediate_redirected:
                                        intermediate_wait_count += 1
                                        if intermediate_wait_count % 10 == 0:  # Print status every 10 seconds
                                            print(f"[INFO] Still waiting for intermediate page redirect... (checked {intermediate_wait_count} times)")
                                        
                                        # If waiting too long (40+ checks) and haven't retried yet, retry the page actions
                                        if intermediate_wait_count >= 40 and not retry_attempted:
                                            print("[WARN] Waiting too long for intermediate page redirect, will retry page actions (tick box and press button)...")
                                            retry_attempted = True
                                            
                                            try:
                                                # Wait for page to be ready
                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                time.sleep(2)
                                                
                                                # Step 1: Find and check privacy checkbox
                                                print("[INFO] Retry: Looking for privacy checkbox...")
                                                privacy_checkbox_retry = None
                                                
                                                # Try multiple ways to find privacy checkbox
                                                privacy_selectors = [
                                                    (By.ID, "ctl00_ContentPlaceHolder1_CheckBoxRead"),
                                                    (By.XPATH, "//input[@type='checkbox' and contains(@id, 'CheckBoxRead')]"),
                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//preceding::input[@type='checkbox'][1]"),
                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//following::input[@type='checkbox'][1]"),
                                                    (By.XPATH, "//input[@type='checkbox'][contains(../text(), 'I acknowledge')]"),
                                                ]
                                                
                                                for by, selector in privacy_selectors:
                                                    try:
                                                        privacy_checkbox_retry = browser.find_element(by, selector)
                                                        if privacy_checkbox_retry.is_displayed():
                                                            print(f"[SUCCESS] Found privacy checkbox for retry: {by}={selector}")
                                                            break
                                                    except:
                                                        continue
                                                
                                                if privacy_checkbox_retry:
                                                    # Scroll to checkbox
                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", privacy_checkbox_retry)
                                                    time.sleep(0.5)
                                                    
                                                    # Check if not already checked
                                                    if not privacy_checkbox_retry.is_selected():
                                                        privacy_checkbox_retry.click()
                                                        print("[SUCCESS] Retry: Privacy checkbox checked")
                                                    else:
                                                        print("[INFO] Retry: Privacy checkbox already checked")
                                                    time.sleep(1)
                                                else:
                                                    print("[WARN] Retry: Privacy checkbox not found, will try to find submit button anyway")
                                                
                                                # Step 2: Find and click submit button
                                                print("[INFO] Retry: Looking for submit button...")
                                                submit_button_retry = None
                                                
                                                submit_selectors = [
                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Save and Continue')]"),
                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Continue')]"),
                                                    (By.XPATH, "//input[@type='button' and contains(@value, 'Continue')]"),
                                                    (By.XPATH, "//button[contains(text(), 'Save and Continue')]"),
                                                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnSave"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnContinue"),
                                                ]
                                                
                                                for by, selector in submit_selectors:
                                                    try:
                                                        submit_button_retry = browser.find_element(by, selector)
                                                        if submit_button_retry.is_displayed() and submit_button_retry.is_enabled():
                                                            print(f"[SUCCESS] Found submit button for retry: {by}={selector}")
                                                            break
                                                    except:
                                                        continue
                                                
                                                if submit_button_retry:
                                                    # Scroll to button
                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button_retry)
                                                    time.sleep(0.5)
                                                    
                                                    # Click button
                                                    try:
                                                        submit_button_retry.click()
                                                        print("[SUCCESS] Retry: Clicked submit button")
                                                    except:
                                                        try:
                                                            browser.execute_script("arguments[0].click();", submit_button_retry)
                                                            print("[SUCCESS] Retry: Clicked submit button using JavaScript")
                                                        except:
                                                            ActionChains(browser).move_to_element(submit_button_retry).click().perform()
                                                            print("[SUCCESS] Retry: Clicked submit button using ActionChains")
                                                    
                                                    # Wait a bit after clicking
                                                    time.sleep(2)
                                                    print("[INFO] Retry: Waiting for page navigation after retry actions...")
                                                    
                                                    # Reset wait count to give it more time after retry
                                                    intermediate_wait_count = 0
                                                else:
                                                    print("[WARN] Retry: Submit button not found")
                                                    
                                            except Exception as retry_error:
                                                print(f"[WARN] Error during retry actions: {retry_error}")
                                        
                                        time.sleep(1)
                                        final_url = browser.current_url
                                        
                                        if final_url != new_url:
                                            print(f"[INFO] Page auto-redirected to: {final_url}")
                                            if "VisaTypeDetails.aspx" in final_url:
                                                print("[SUCCESS] Navigated to form page from intermediate page")
                                                navigated = True
                                                intermediate_redirected = True
                                                break
                                            elif "OnlineHome.aspx" in final_url:
                                                print("[WARN] Intermediate page redirected to homepage")
                                                intermediate_redirected = True
                                                break
                                        
                                        # Check document ready state and final URL
                                        try:
                                            ready_state = browser.execute_script("return document.readyState")
                                            if ready_state == "complete":
                                                time.sleep(1)
                                                final_check = browser.current_url
                                                if "VisaTypeDetails.aspx" in final_check:
                                                    print("[SUCCESS] Navigated to form page after page complete")
                                                    navigated = True
                                                    intermediate_redirected = True
                                                    break
                                                elif "OnlineHome.aspx" in final_check:
                                                    print("[WARN] Intermediate page redirected to homepage after page complete")
                                                    intermediate_redirected = True
                                                    break
                                        except:
                                            pass
                                        # Check if page is ready and might have JavaScript redirect
                                        try:
                                            ready_state = browser.execute_script("return document.readyState")
                                            if ready_state == "complete":
                                                # Check for any redirects after page is complete
                                                time.sleep(1)
                                                final_url = browser.current_url
                                                if "VisaTypeDetails.aspx" in final_url:
                                                    print("[SUCCESS] Navigated to form page after page complete")
                                                    navigated = True
                                                    break
                                        except:
                                            pass
                                    
                                    if not navigated and "OnlineHome.aspx" in browser.current_url:
                                        print("[WARN] Intermediate page redirected to homepage, will try to navigate from homepage")
                                elif "OnlineHome.aspx" in new_url:
                                    print("[WARN] Detected homepage URL (OnlineHome.aspx), waiting to confirm if page is stable...")
                                    # Wait a bit to see if page continues to navigate (might be temporary redirect)
                                    time.sleep(3)
                                    stable_url = browser.current_url
                                    
                                    # Check if page is still on homepage or has navigated elsewhere
                                    if "VisaTypeDetails.aspx" in stable_url:
                                        print("[SUCCESS] Page navigated to form page after temporary homepage redirect")
                                        navigated = True
                                        break
                                    elif "OnlineHome2.aspx" in stable_url:
                                        print("[INFO] Page navigated to intermediate page after temporary homepage redirect")
                                        # Continue waiting for final navigation
                                        continue
                                    elif "OnlineHome.aspx" in stable_url:
                                        # Page is stable on homepage, confirm it's really the homepage
                                        print("[WARN] Page is stable on homepage (OnlineHome.aspx), confirming...")
                                        time.sleep(2)
                                        final_confirm_url = browser.current_url
                                        if "VisaTypeDetails.aspx" in final_confirm_url:
                                            print("[SUCCESS] Page navigated to form page after homepage confirmation")
                                            navigated = True
                                            break
                                        elif "OnlineHome2.aspx" in final_confirm_url:
                                            print("[INFO] Page navigated to intermediate page after homepage confirmation")
                                            continue
                                        else:
                                            # Really on homepage, try to navigate
                                            print("[WARN] Confirmed: Redirected to homepage (OnlineHome.aspx)")
                                            
                                            # Try to navigate from homepage by clicking Continue button
                                            print("[INFO] Attempting to navigate from homepage by clicking Continue button...")
                                            try:
                                                # Wait for page to load
                                                time.sleep(2)
                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                
                                                # Find and click the Continue button on homepage
                                                continue_button_selectors = [
                                                    (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
                                                    (By.XPATH, "//input[@type='submit' and @value='Continue']"),
                                                    (By.XPATH, "//input[@name='ctl00$ContentPlaceHolder1$applyNow']"),
                                                ]
                                                
                                                continue_button = None
                                                for by, selector in continue_button_selectors:
                                                    try:
                                                        continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                                                        print(f"[SUCCESS] Found homepage Continue button: {by}={selector}")
                                                        break
                                                    except (TimeoutException, NoSuchElementException):
                                                        continue
                                                
                                                if continue_button:
                                                    homepage_url = browser.current_url
                                                    continue_button.click()
                                                    print("[SUCCESS] Clicked homepage Continue button")
                                                    
                                                    # Wait for navigation - wait indefinitely until redirect to form page or homepage
                                                    print("[INFO] Waiting for navigation to form page...")
                                                    navigation_wait_count = 0
                                                    navigation_completed = False
                                                    while not navigation_completed:
                                                        navigation_wait_count += 1
                                                        if navigation_wait_count % 10 == 0:  # Print status every 10 seconds
                                                            print(f"[INFO] Still waiting for navigation... (checked {navigation_wait_count} times)")
                                                        
                                                        time.sleep(1)
                                                        new_url_after_continue = browser.current_url
                                                        
                                                        if new_url_after_continue != homepage_url:
                                                            print(f"[INFO] URL changed after Continue click: {new_url_after_continue}")
                                                            if "VisaTypeDetails.aspx" in new_url_after_continue:
                                                                print("[SUCCESS] Navigated to form page from homepage")
                                                                navigated = True
                                                                navigation_completed = True
                                                                break
                                                            elif "OnlineHome2.aspx" in new_url_after_continue:
                                                                print("[INFO] On intermediate page after Continue, calling handle_intermediate_page immediately...")
                                                                # Immediately call handle_intermediate_page to tick checkbox and click submit
                                                                if handle_intermediate_page(browser, wait):
                                                                    print("[SUCCESS] Successfully navigated to form page from intermediate page")
                                                                    navigated = True
                                                                    navigation_completed = True
                                                                    break
                                                                else:
                                                                    print("[WARN] handle_intermediate_page returned False, waiting for redirect...")
                                                                    # Wait for intermediate page to redirect
                                                                    intermediate_wait_count = 0
                                                                    intermediate_redirected = False
                                                                    retry_attempted = False  # Track if we've already retried
                                                                    while not intermediate_redirected:
                                                                        intermediate_wait_count += 1
                                                                        if intermediate_wait_count % 10 == 0:
                                                                            print(f"[INFO] Still waiting for intermediate page redirect... (checked {intermediate_wait_count} times)")
                                                                        
                                                                        # If waiting too long (40+ checks) and haven't retried yet, retry the page actions
                                                                        if intermediate_wait_count >= 40 and not retry_attempted:
                                                                            print("[WARN] Waiting too long for intermediate page redirect, will retry page actions (tick box and press button)...")
                                                                            retry_attempted = True
                                                                            
                                                                            # Call handle_intermediate_page again
                                                                            if handle_intermediate_page(browser, wait):
                                                                                print("[SUCCESS] Successfully navigated to form page after retry")
                                                                                navigated = True
                                                                                navigation_completed = True
                                                                                intermediate_redirected = True
                                                                                break
                                                                            
                                                                            # If handle_intermediate_page didn't work, try manual retry
                                                                            try:
                                                                                # Wait for page to be ready
                                                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                                                time.sleep(2)
                                                                                
                                                                                # Step 1: Find and check privacy checkbox
                                                                                print("[INFO] Retry: Looking for privacy checkbox...")
                                                                                privacy_checkbox_retry = None
                                                                                
                                                                                # Try multiple ways to find privacy checkbox
                                                                                privacy_selectors = [
                                                                                    (By.ID, "ctl00_ContentPlaceHolder1_CheckBoxRead"),
                                                                                    (By.XPATH, "//input[@type='checkbox' and contains(@id, 'CheckBoxRead')]"),
                                                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//preceding::input[@type='checkbox'][1]"),
                                                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//following::input[@type='checkbox'][1]"),
                                                                                    (By.XPATH, "//input[@type='checkbox'][contains(../text(), 'I acknowledge')]"),
                                                                                ]
                                                                                
                                                                                for by, selector in privacy_selectors:
                                                                                    try:
                                                                                        privacy_checkbox_retry = browser.find_element(by, selector)
                                                                                        if privacy_checkbox_retry.is_displayed():
                                                                                            print(f"[SUCCESS] Found privacy checkbox for retry: {by}={selector}")
                                                                                            break
                                                                                    except:
                                                                                        continue
                                                                                
                                                                                if privacy_checkbox_retry:
                                                                                    # Scroll to checkbox
                                                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", privacy_checkbox_retry)
                                                                                    time.sleep(0.5)
                                                                                    
                                                                                    # Check if not already checked
                                                                                    if not privacy_checkbox_retry.is_selected():
                                                                                        privacy_checkbox_retry.click()
                                                                                        print("[SUCCESS] Retry: Privacy checkbox checked")
                                                                                    else:
                                                                                        print("[INFO] Retry: Privacy checkbox already checked")
                                                                                    time.sleep(1)
                                                                                else:
                                                                                    print("[WARN] Retry: Privacy checkbox not found, will try to find submit button anyway")
                                                                                
                                                                                # Step 2: Find and click submit button
                                                                                print("[INFO] Retry: Looking for submit button...")
                                                                                submit_button_retry = None
                                                                                
                                                                                submit_selectors = [
                                                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Save and Continue')]"),
                                                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Continue')]"),
                                                                                    (By.XPATH, "//input[@type='button' and contains(@value, 'Continue')]"),
                                                                                    (By.XPATH, "//button[contains(text(), 'Save and Continue')]"),
                                                                                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                                                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnSave"),
                                                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnContinue"),
                                                                                ]
                                                                                
                                                                                for by, selector in submit_selectors:
                                                                                    try:
                                                                                        submit_button_retry = browser.find_element(by, selector)
                                                                                        if submit_button_retry.is_displayed() and submit_button_retry.is_enabled():
                                                                                            print(f"[SUCCESS] Found submit button for retry: {by}={selector}")
                                                                                            break
                                                                                    except:
                                                                                        continue
                                                                                
                                                                                if submit_button_retry:
                                                                                    # Scroll to button
                                                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button_retry)
                                                                                    time.sleep(0.5)
                                                                                    
                                                                                    # Click button
                                                                                    try:
                                                                                        submit_button_retry.click()
                                                                                        print("[SUCCESS] Retry: Clicked submit button")
                                                                                    except:
                                                                                        try:
                                                                                            browser.execute_script("arguments[0].click();", submit_button_retry)
                                                                                            print("[SUCCESS] Retry: Clicked submit button using JavaScript")
                                                                                        except:
                                                                                            ActionChains(browser).move_to_element(submit_button_retry).click().perform()
                                                                                            print("[SUCCESS] Retry: Clicked submit button using ActionChains")
                                                                                    
                                                                                    # Wait a bit after clicking
                                                                                    time.sleep(2)
                                                                                    print("[INFO] Retry: Waiting for page navigation after retry actions...")
                                                                                    
                                                                                    # Reset wait count to give it more time after retry
                                                                                    intermediate_wait_count = 0
                                                                                else:
                                                                                    print("[WARN] Retry: Submit button not found")
                                                                            
                                                                            except Exception as retry_error:
                                                                                print(f"[WARN] Error during retry actions: {retry_error}")
                                                                    
                                                                    time.sleep(1)
                                                                    final_check = browser.current_url
                                                                    
                                                                    if "VisaTypeDetails.aspx" in final_check:
                                                                        print("[SUCCESS] Navigated to form page from intermediate page")
                                                                        navigated = True
                                                                        navigation_completed = True
                                                                        intermediate_redirected = True
                                                                        break
                                                                    elif "OnlineHome.aspx" in final_check:
                                                                        print("[WARN] Intermediate page redirected to homepage")
                                                                        navigation_completed = True
                                                                        intermediate_redirected = True
                                                                        break
                                                                    
                                                                    # Check document ready state
                                                                    try:
                                                                        ready_state = browser.execute_script("return document.readyState")
                                                                        if ready_state == "complete":
                                                                            time.sleep(1)
                                                                            final_check_after_ready = browser.current_url
                                                                            if "VisaTypeDetails.aspx" in final_check_after_ready:
                                                                                print("[SUCCESS] Navigated to form page after page complete")
                                                                                navigated = True
                                                                                navigation_completed = True
                                                                                intermediate_redirected = True
                                                                                break
                                                                            elif "OnlineHome.aspx" in final_check_after_ready:
                                                                                print("[WARN] Intermediate page redirected to homepage after page complete")
                                                                                navigation_completed = True
                                                                                intermediate_redirected = True
                                                                                break
                                                                    except:
                                                                        pass
                                                                
                                                                if navigation_completed:
                                                                    break
                                                            elif "OnlineHome.aspx" in new_url_after_continue:
                                                                print("[WARN] Redirected back to homepage")
                                                                navigation_completed = True
                                                                break
                                                        
                                                        # Check document ready state
                                                        try:
                                                            ready_state = browser.execute_script("return document.readyState")
                                                            if ready_state == "complete":
                                                                time.sleep(1)
                                                                final_check = browser.current_url
                                                                if "VisaTypeDetails.aspx" in final_check:
                                                                    print("[SUCCESS] Navigated to form page after page complete")
                                                                    navigated = True
                                                                    navigation_completed = True
                                                                    break
                                                                elif "OnlineHome.aspx" in final_check and final_check != homepage_url:
                                                                    print("[WARN] Redirected to homepage after page complete")
                                                                    navigation_completed = True
                                                                    break
                                                        except:
                                                            pass
                                                    
                                                    if navigated:
                                                        break
                                                else:
                                                    print("[WARN] Could not find Continue button on homepage")
                                            except Exception as e:
                                                print(f"[WARN] Error trying to navigate from homepage: {e}")
                                    
                                    if not navigated:
                                        print("[WARN] Could not navigate to form page from homepage")
                                    break
                            
                            # Check if page is ready
                            if ready_state == "complete":
                                # Wait a bit more for any redirects
                                time.sleep(2)
                                final_url = browser.current_url
                                if "VisaTypeDetails.aspx" in final_url:
                                    print("[SUCCESS] Form page loaded")
                                    navigated = True
                                    break
                                elif final_url != new_url:
                                    print(f"[INFO] Page redirected to: {final_url}")
                            
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"[DEBUG] Navigation check error: {e}")
                            time.sleep(0.5)
                    
                    if not navigated:
                        print("[WARN] Page navigation timeout or redirected to unexpected page")
                        print(f"[INFO] Final URL: {browser.current_url}")
                    
                    # Additional wait to ensure page is fully loaded
                    time.sleep(2)
                else:
                    print("[WARN] Submit button not found, may need to click manually")
                    
            except Exception as e:
                print(f"[ERROR] Error checking checkbox: {e}")
        else:
            print("[WARN] Privacy checkbox not found, trying to find all checkboxes...")
            # Last attempt: find all unchecked checkboxes
            try:
                all_checkboxes = browser.find_elements(By.XPATH, "//input[@type='checkbox']")
                if len(all_checkboxes) > 0:
                    print(f"[INFO] Found {len(all_checkboxes)} checkboxes, trying to check first unchecked one...")
                    for checkbox in all_checkboxes:
                        if not checkbox.is_selected():
                            checkbox.click()
                            print("[SUCCESS] Checkbox checked")
                            time.sleep(1)
                            # Find submit button
                            submit_buttons = browser.find_elements(By.XPATH, "//input[@type='submit']")
                            if submit_buttons:
                                # Record current URL before clicking
                                current_url = browser.current_url
                                print(f"[INFO] Current URL before clicking submit: {current_url}")
                                
                                submit_buttons[0].click()
                                print("[SUCCESS] Clicked submit button")
                                
                                # Wait for page navigation
                                print("[INFO] Waiting for page navigation after clicking submit...")
                                max_wait = 20
                                start_time = time.time()
                                
                                while time.time() - start_time < max_wait:
                                    try:
                                        new_url = browser.current_url
                                        if new_url != current_url:
                                            print(f"[INFO] URL changed to: {new_url}")
                                            if "VisaTypeDetails.aspx" in new_url:
                                                print("[SUCCESS] Navigated to form page")
                                                break
                                            elif "OnlineHome2.aspx" in new_url:
                                                print("[INFO] On intermediate page, waiting for final navigation...")
                                                time.sleep(2)
                                        time.sleep(0.5)
                                    except:
                                        time.sleep(0.5)
                                
                                time.sleep(2)
                            break
            except Exception as e:
                print(f"[ERROR] Error finding checkboxes: {e}")

        # ------------------------------------------------
        # Step 3: Check if entered the application form page
        # ------------------------------------------------
        print(f"[INFO] Current page URL: {browser.current_url}")
        print(f"[INFO] Current page title: {browser.title}")
        
        # Check if we're on the form page or need to navigate
        current_url_final = browser.current_url
        if "OnlineHome.aspx" in current_url_final or "OnlineHome2.aspx" in current_url_final:
            print("[WARN] Still on homepage or intermediate page, attempting to navigate to form page...")
            # Try one more time to navigate from homepage
            try:
                if "OnlineHome.aspx" in current_url_final:
                    # Wait for page to fully load
                    time.sleep(2)
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    
                    # Find and click Continue button
                    continue_button_selectors = [
                        (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
                        (By.XPATH, "//input[@type='submit' and @value='Continue']"),
                        (By.XPATH, "//input[@name='ctl00$ContentPlaceHolder1$applyNow']"),
                    ]
                    
                    continue_button = None
                    for by, selector in continue_button_selectors:
                        try:
                            continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                            print(f"[SUCCESS] Found homepage Continue button: {by}={selector}")
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue
                    
                    if continue_button:
                        homepage_url = browser.current_url
                        continue_button.click()
                        print("[SUCCESS] Clicked Continue button from homepage")
                        
                        # Wait for navigation - wait indefinitely until redirect to form page or homepage
                        print("[INFO] Waiting for navigation to form page...")
                        navigation_wait_count = 0
                        navigated_to_form = False
                        navigation_completed = False
                        while not navigation_completed:
                            navigation_wait_count += 1
                            if navigation_wait_count % 10 == 0:  # Print status every 10 seconds
                                print(f"[INFO] Still waiting for navigation... (checked {navigation_wait_count} times)")
                            
                            time.sleep(1)
                            new_url_after_continue = browser.current_url
                            
                            if new_url_after_continue != homepage_url:
                                print(f"[INFO] URL changed after Continue click: {new_url_after_continue}")
                                if "VisaTypeDetails.aspx" in new_url_after_continue:
                                    print("[SUCCESS] Navigated to form page from homepage")
                                    navigated_to_form = True
                                    navigation_completed = True
                                    break
                                elif "OnlineHome2.aspx" in new_url_after_continue:
                                    print("[INFO] On intermediate page after Continue, waiting for redirect...")
                                    # Wait for intermediate page to redirect indefinitely
                                    intermediate_wait_count = 0
                                    intermediate_redirected = False
                                    retry_attempted = False  # Track if we've already retried
                                    while not intermediate_redirected:
                                        intermediate_wait_count += 1
                                        if intermediate_wait_count % 10 == 0:
                                            print(f"[INFO] Still waiting for intermediate page redirect... (checked {intermediate_wait_count} times)")
                                        
                                        # If waiting too long (40+ checks) and haven't retried yet, retry the page actions
                                        if intermediate_wait_count >= 40 and not retry_attempted:
                                            print("[WARN] Waiting too long for intermediate page redirect, will retry page actions (tick box and press button)...")
                                            retry_attempted = True
                                            
                                            try:
                                                # Wait for page to be ready
                                                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                                                time.sleep(2)
                                                
                                                # Step 1: Find and check privacy checkbox
                                                print("[INFO] Retry: Looking for privacy checkbox...")
                                                privacy_checkbox_retry = None
                                                
                                                # Try multiple ways to find privacy checkbox
                                                privacy_selectors = [
                                                    (By.ID, "ctl00_ContentPlaceHolder1_CheckBoxRead"),
                                                    (By.XPATH, "//input[@type='checkbox' and contains(@id, 'CheckBoxRead')]"),
                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//preceding::input[@type='checkbox'][1]"),
                                                    (By.XPATH, "//label[contains(text(), 'I acknowledge that I have read and understood')]//following::input[@type='checkbox'][1]"),
                                                    (By.XPATH, "//input[@type='checkbox'][contains(../text(), 'I acknowledge')]"),
                                                ]
                                                
                                                for by, selector in privacy_selectors:
                                                    try:
                                                        privacy_checkbox_retry = browser.find_element(by, selector)
                                                        if privacy_checkbox_retry.is_displayed():
                                                            print(f"[SUCCESS] Found privacy checkbox for retry: {by}={selector}")
                                                            break
                                                    except:
                                                        continue
                                                
                                                if privacy_checkbox_retry:
                                                    # Scroll to checkbox
                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", privacy_checkbox_retry)
                                                    time.sleep(0.5)
                                                    
                                                    # Check if not already checked
                                                    if not privacy_checkbox_retry.is_selected():
                                                        privacy_checkbox_retry.click()
                                                        print("[SUCCESS] Retry: Privacy checkbox checked")
                                                    else:
                                                        print("[INFO] Retry: Privacy checkbox already checked")
                                                    time.sleep(1)
                                                else:
                                                    print("[WARN] Retry: Privacy checkbox not found, will try to find submit button anyway")
                                                
                                                # Step 2: Find and click submit button
                                                print("[INFO] Retry: Looking for submit button...")
                                                submit_button_retry = None
                                                
                                                submit_selectors = [
                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Save and Continue')]"),
                                                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Continue')]"),
                                                    (By.XPATH, "//input[@type='button' and contains(@value, 'Continue')]"),
                                                    (By.XPATH, "//button[contains(text(), 'Save and Continue')]"),
                                                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnSave"),
                                                    (By.ID, "ctl00_ContentPlaceHolder1_btnContinue"),
                                                ]
                                                
                                                for by, selector in submit_selectors:
                                                    try:
                                                        submit_button_retry = browser.find_element(by, selector)
                                                        if submit_button_retry.is_displayed() and submit_button_retry.is_enabled():
                                                            print(f"[SUCCESS] Found submit button for retry: {by}={selector}")
                                                            break
                                                    except:
                                                        continue
                                                
                                                if submit_button_retry:
                                                    # Scroll to button
                                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button_retry)
                                                    time.sleep(0.5)
                                                    
                                                    # Click button
                                                    try:
                                                        submit_button_retry.click()
                                                        print("[SUCCESS] Retry: Clicked submit button")
                                                    except:
                                                        try:
                                                            browser.execute_script("arguments[0].click();", submit_button_retry)
                                                            print("[SUCCESS] Retry: Clicked submit button using JavaScript")
                                                        except:
                                                            ActionChains(browser).move_to_element(submit_button_retry).click().perform()
                                                            print("[SUCCESS] Retry: Clicked submit button using ActionChains")
                                                    
                                                    # Wait a bit after clicking
                                                    time.sleep(2)
                                                    print("[INFO] Retry: Waiting for page navigation after retry actions...")
                                                    
                                                    # Reset wait count to give it more time after retry
                                                    intermediate_wait_count = 0
                                                else:
                                                    print("[WARN] Retry: Submit button not found")
                                                    
                                            except Exception as retry_error:
                                                print(f"[WARN] Error during retry actions: {retry_error}")
                                        
                                        time.sleep(1)
                                        final_check = browser.current_url
                                        
                                        if "VisaTypeDetails.aspx" in final_check:
                                            print("[SUCCESS] Navigated to form page from intermediate page")
                                            navigated_to_form = True
                                            navigation_completed = True
                                            intermediate_redirected = True
                                            break
                                        elif "OnlineHome.aspx" in final_check:
                                            print("[WARN] Intermediate page redirected to homepage")
                                            navigation_completed = True
                                            intermediate_redirected = True
                                            break
                                        
                                        # Check document ready state
                                        try:
                                            ready_state = browser.execute_script("return document.readyState")
                                            if ready_state == "complete":
                                                time.sleep(1)
                                                final_check_after_ready = browser.current_url
                                                if "VisaTypeDetails.aspx" in final_check_after_ready:
                                                    print("[SUCCESS] Navigated to form page after page complete")
                                                    navigated_to_form = True
                                                    navigation_completed = True
                                                    intermediate_redirected = True
                                                    break
                                                elif "OnlineHome.aspx" in final_check_after_ready:
                                                    print("[WARN] Intermediate page redirected to homepage after page complete")
                                                    navigation_completed = True
                                                    intermediate_redirected = True
                                                    break
                                        except:
                                            pass
                                    
                                    if navigation_completed:
                                        break
                                elif "OnlineHome.aspx" in new_url_after_continue:
                                    print("[WARN] Redirected back to homepage")
                                    navigation_completed = True
                                    break
                            
                            # Check document ready state
                            try:
                                ready_state = browser.execute_script("return document.readyState")
                                if ready_state == "complete":
                                    time.sleep(1)
                                    final_check = browser.current_url
                                    if "VisaTypeDetails.aspx" in final_check:
                                        print("[SUCCESS] Navigated to form page after page complete")
                                        navigated_to_form = True
                                        navigation_completed = True
                                        break
                                    elif "OnlineHome.aspx" in final_check and final_check != homepage_url:
                                        print("[WARN] Redirected to homepage after page complete")
                                        navigation_completed = True
                                        break
                            except:
                                pass
                        
                        if navigated_to_form:
                            time.sleep(2)  # Additional wait for page to fully load
                        else:
                            print("[WARN] Did not navigate to form page after clicking Continue from homepage")
                    else:
                        print("[WARN] Could not find Continue button on homepage")
                elif "OnlineHome2.aspx" in current_url_final:
                    # Wait for intermediate page to redirect - wait indefinitely until redirect to form page or homepage
                    print("[INFO] Waiting for intermediate page to redirect to form page...")
                    intermediate_wait_count = 0
                    intermediate_redirected = False
                    while not intermediate_redirected:
                        intermediate_wait_count += 1
                        if intermediate_wait_count % 10 == 0:  # Print status every 10 seconds
                            print(f"[INFO] Still waiting for intermediate page redirect... (checked {intermediate_wait_count} times)")
                        
                        time.sleep(1)
                        final_url_check = browser.current_url
                        
                        if "VisaTypeDetails.aspx" in final_url_check:
                            print("[SUCCESS] Intermediate page redirected to form page")
                            intermediate_redirected = True
                            break
                        elif "OnlineHome.aspx" in final_url_check:
                            print("[WARN] Intermediate page redirected to homepage")
                            intermediate_redirected = True
                            break
                        
                        # Check document ready state
                        try:
                            ready_state = browser.execute_script("return document.readyState")
                            if ready_state == "complete":
                                time.sleep(1)
                                final_url_check_after_ready = browser.current_url
                                if "VisaTypeDetails.aspx" in final_url_check_after_ready:
                                    print("[SUCCESS] Intermediate page redirected to form page after page complete")
                                    intermediate_redirected = True
                                    break
                                elif "OnlineHome.aspx" in final_url_check_after_ready:
                                    print("[WARN] Intermediate page redirected to homepage after page complete")
                                    intermediate_redirected = True
                                    break
                        except:
                            pass
            except Exception as e:
                print(f"[WARN] Error attempting final navigation: {e}")
        
        # Check if on form page (usually has input fields)
        final_url_check = browser.current_url
        if "VisaTypeDetails.aspx" in final_url_check:
            try:
                form_inputs = browser.find_elements(By.TAG_NAME, "input")
                if len(form_inputs) > 0:
                    print(f"[SUCCESS] Entered application form page, found {len(form_inputs)} input fields")
                else:
                    print("[INFO] Current page may not be a form page")
            except:
                pass
        else:
            print(f"[WARN] Not on form page, current URL: {final_url_check}")
            print("[WARN] You may need to manually navigate to the form page")

        print("\n[INFO] Automation process completed, browser will remain open")
        print("[INFO] You can now manually fill the form or continue with automation")
        
        # Call the form filling function only if we're on the form page
        final_url_before_fill = browser.current_url
        if "VisaTypeDetails.aspx" in final_url_before_fill:
            print("\n[INFO] Starting automatic form filling...")
            fill_application_form(browser, wait)
        else:
            print("\n[WARN] Skipping automatic form filling - not on form page")
            print(f"[INFO] Current URL: {final_url_before_fill}")
            print("[INFO] Please manually navigate to the form page and run the form filling function")

    except Exception as e:
        print(f"[ERROR] Error during execution: {e}")
        import traceback
        traceback.print_exc()

    # ------------------------------------------------
    # Program continues running, browser will not close
    # ------------------------------------------------
    input("\nPress Enter to exit and close browser...")
    browser.quit()



def fill_application_form(browser, wait, enable_screenshots=False, screenshots_dir="screenshots"):
    """
    Automatically fill the visa application form page by page

    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        enable_screenshots: If True, take a screenshot after each page fill.
                            Screenshots are saved to screenshots_dir and named
                            page_N_after_fill_YYYYMMDD_HHMMSS.png.
        screenshots_dir: Directory where screenshots are saved (default: "screenshots").
    """
    def _screenshot(label):
        if enable_screenshots:
            take_screenshot(browser, label, output_dir=screenshots_dir)

    try:
        print("\n" + "="*60)
        print("Starting form filling process...")
        print("="*60)
        
        # Check for error page first
        error_result = check_and_handle_error_page(browser, wait)
        if error_result == "homepage_redirect":
            log_operation("fill_application_form", "WARN", "Error page handling redirected to homepage - checking for Application Number...")
            # Check for saved Application Number - if found, retrieve application instead of clicking Continue
            saved_app_number = get_saved_application_number()
            if saved_app_number:
                log_operation("fill_application_form", "INFO", f"Found Application Number: {saved_app_number}, retrieving application instead of clicking Continue...")
                if retrieve_application(browser, wait, saved_app_number):
                    log_operation("fill_application_form", "SUCCESS", "Successfully retrieved application, re-starting form filling process...")
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "WARN", "Failed to retrieve application, trying restart_from_homepage...")
            # If no Application Number or retrieval failed, use restart_from_homepage
            if restart_from_homepage(browser, wait):
                log_operation("fill_application_form", "INFO", "Successfully restarted from homepage, re-starting form filling process...")
                return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
            else:
                log_operation("fill_application_form", "ERROR", "Failed to restart from homepage")
                return
        elif error_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected - stopping all page filling")
            return
        
        # First, check if we're on the correct form page
        current_url = browser.current_url
        print(f"[INFO] Current URL at start: {current_url}")
        
        # If not on form page, try to navigate to it
        if "VisaTypeDetails.aspx" not in current_url:
            print("[WARN] Not on form page, attempting to navigate to form page...")
            
            # Check if we're on the homepage (OnlineHome.aspx)
            if "OnlineHome.aspx" in current_url:
                print("[INFO] Currently on homepage, checking for Application Number...")
                
                # Check for saved Application Number first
                # Note: We don't extract from page here, only check saved file
                # Application Number extraction happens in fill_page_4/fill_page_5
                saved_app_number = get_saved_application_number()
                
                app_number_to_use = None
                if saved_app_number:
                    app_number_to_use = saved_app_number
                    log_operation("fill_application_form", "INFO", f"Using saved Application Number: {saved_app_number}")
                
                # If Application Number found, retrieve application instead of clicking Continue
                if app_number_to_use:
                    log_operation("fill_application_form", "INFO", f"Application Number found: {app_number_to_use}, retrieving application...")
                    if retrieve_application(browser, wait, app_number_to_use):
                        log_operation("fill_application_form", "SUCCESS", "Successfully retrieved application")
                        # Wait for page to load
                        time.sleep(3)
                        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        time.sleep(2)
                        # Check if we're now on form page
                        new_url = browser.current_url
                        if "VisaTypeDetails.aspx" in new_url:
                            log_operation("fill_application_form", "SUCCESS", "After retrieving application, on form page - continuing with form filling")
                            # Continue with form filling (skip the Continue button click)
                            # The code will continue below to fill the form
                        else:
                            log_operation("fill_application_form", "INFO", f"After retrieving application, on page: {new_url}")
                            # Continue with normal flow
                    else:
                        log_operation("fill_application_form", "WARN", "Failed to retrieve application, will try Continue button instead")
                        # Fall through to Continue button logic
                else:
                    log_operation("fill_application_form", "INFO", "No Application Number found, proceeding with Continue button")
                
                # Only click Continue button if no Application Number was found or retrieval failed
                if not app_number_to_use or "VisaTypeDetails.aspx" not in browser.current_url:
                    print("[INFO] Need to click 'Continue' button to enter form page")
                try:
                    # Find and click the "Continue" button on homepage
                    # The button ID is: ctl00_ContentPlaceHolder1_applyNow
                    continue_button_selectors = [
                        (By.ID, "ctl00_ContentPlaceHolder1_applyNow"),
                        (By.XPATH, "//input[@type='submit' and @value='Continue']"),
                        (By.XPATH, "//input[@name='ctl00$ContentPlaceHolder1$applyNow']"),
                    ]
                    
                    continue_button = None
                    for by, selector in continue_button_selectors:
                        try:
                            continue_button = wait.until(EC.element_to_be_clickable((by, selector)))
                            print(f"[SUCCESS] Found homepage Continue button: {by}={selector}")
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue
                    
                    if continue_button:
                        # Record URL before clicking
                        url_before = browser.current_url
                        print(f"[INFO] URL before clicking homepage Continue: {url_before}")
                        
                        # Click the button
                        continue_button.click()
                        print("[SUCCESS] Clicked homepage Continue button")
                        
                        # Wait for navigation to form page
                        print("[INFO] Waiting for navigation to form page...")
                        max_wait = 20
                        start_time = time.time()
                        navigated = False
                        
                        while time.time() - start_time < max_wait:
                            try:
                                new_url = browser.current_url
                                ready_state = browser.execute_script("return document.readyState")
                                
                                if new_url != url_before:
                                    print(f"[INFO] URL changed to: {new_url}")
                                    
                                    if "VisaTypeDetails.aspx" in new_url:
                                        print("[SUCCESS] Navigated to form page!")
                                        navigated = True
                                        break
                                    elif "OnlineHome2.aspx" in new_url:
                                        print("[INFO] On intermediate page (OnlineHome2.aspx), waiting...")
                                        time.sleep(2)
                                        # Check if it redirects to form page
                                        final_url = browser.current_url
                                        if "VisaTypeDetails.aspx" in final_url:
                                            navigated = True
                                            break
                                    elif "OnlineHome.aspx" in new_url:
                                        print("[WARN] Still on homepage, may need to wait longer...")
                                
                                if ready_state == "complete":
                                    time.sleep(1)
                                    final_check = browser.current_url
                                    if "VisaTypeDetails.aspx" in final_check:
                                        navigated = True
                                        break
                                
                                time.sleep(0.5)
                            except Exception as e:
                                print(f"[DEBUG] Navigation check error: {e}")
                                time.sleep(0.5)
                        
                        if not navigated:
                            print("[WARN] Did not navigate to form page after clicking Continue")
                            print(f"[INFO] Current URL: {browser.current_url}")
                            return
                        
                        # Additional wait for form page to fully load
                        time.sleep(3)
                    else:
                        print("[WARN] Could not find homepage Continue button")
                        return
                except Exception as e:
                    print(f"[ERROR] Error clicking homepage Continue button: {e}")
                    return
            else:
                # If on some other page, try direct navigation (but this may not work due to session)
                print("[WARN] On unexpected page, attempting direct navigation (may fail due to session)...")
                try:
                    form_url = "https://www.visas.inis.gov.ie/AVATS/VisaTypeDetails.aspx"
                    browser.get(form_url)
                    print(f"[INFO] Navigated to: {form_url}")
                    time.sleep(3)
                    
                    # Wait for page to load
                    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                    
                    # Check if we're redirected back to homepage
                    new_url = browser.current_url
                    if "OnlineHome.aspx" in new_url:
                        log_operation("fill_application_form", "WARN", "Direct navigation redirected to homepage - restarting from homepage")
                        # Restart from homepage instead of continuing form filling
                        if restart_from_homepage(browser, wait):
                            log_operation("fill_application_form", "INFO", "Successfully restarted from homepage, stopping form filling to restart process")
                            return
                        else:
                            log_operation("fill_application_form", "ERROR", "Failed to restart from homepage, stopping form filling")
                            return
                except Exception as e:
                    print(f"[WARN] Error navigating to form page: {e}")
                    return
        
        # Wait for page to be fully loaded before starting
        print("[INFO] Waiting for form page to fully load...")
        time.sleep(5)  # Initial wait
        
        # Wait for document ready state
        try:
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            print("[SUCCESS] Document ready state is complete")
        except:
            print("[WARN] Document ready state check timeout, continuing anyway...")
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Check for error page before proceeding
        check_and_handle_error_page(browser, wait)
        
        # Check current page again
        final_url = browser.current_url
        print(f"[INFO] Current URL: {final_url}")
        print(f"[INFO] Current page title: {browser.title}")
        
        # Verify we're still on the form page (not redirected)
        if "OnlineHome.aspx" in final_url or "OnlineHome2.aspx" in final_url:
            log_operation("fill_application_form", "WARN", "Page appears to have redirected away from form page!")
            log_operation("fill_application_form", "WARN", "This might be due to session timeout or form validation")
            
            # Restart from homepage instead of continuing form filling
            if "OnlineHome.aspx" in final_url:
                log_operation("fill_application_form", "INFO", "Detected redirect to homepage - restarting from homepage")
                if restart_from_homepage(browser, wait):
                    log_operation("fill_application_form", "INFO", "Successfully restarted from homepage, stopping form filling to restart process")
                    return
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage, stopping form filling")
                    return
            elif "OnlineHome2.aspx" in final_url:
                log_operation("fill_application_form", "INFO", "On intermediate page, calling handle_intermediate_page function...")
                if handle_intermediate_page(browser, wait):
                    log_operation("fill_application_form", "INFO", "Successfully navigated to form page from intermediate page, continuing...")
                    # Continue with form filling
                else:
                    log_operation("fill_application_form", "WARN", "Failed to navigate from intermediate page, checking current URL...")
                    final_check = browser.current_url
                    if "OnlineHome.aspx" in final_check:
                        log_operation("fill_application_form", "INFO", "Intermediate page redirected to homepage - restarting from homepage")
                        if restart_from_homepage(browser, wait):
                            log_operation("fill_application_form", "INFO", "Successfully restarted from homepage, stopping form filling to restart process")
                            return
                        else:
                            log_operation("fill_application_form", "ERROR", "Failed to restart from homepage, stopping form filling")
                            return
                    elif "VisaTypeDetails.aspx" in final_check:
                        log_operation("fill_application_form", "INFO", "Intermediate page redirected to form page, continuing...")
                    else:
                        log_operation("fill_application_form", "WARN", f"Unexpected URL after intermediate page: {final_check}")
                        return
        
        # Try to find any form elements to confirm page is loaded
        try:
            all_inputs = browser.find_elements(By.TAG_NAME, "input")
            all_selects = browser.find_elements(By.TAG_NAME, "select")
            print(f"[INFO] Found {len(all_inputs)} input fields and {len(all_selects)} select fields")
            
            if len(all_inputs) == 0:
                print("[WARN] No input fields found, page may not be the form page")
        except:
            pass
        
        # Fill Page 1
        page_1_result = fill_page_1(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_1_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 1 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        # Check if page 1 was interrupted due to homepage redirect or other issues
        if page_1_result == False or page_1_result == "homepage_redirect":
            log_operation("fill_application_form", "WARN", f"Page 1 returned: {page_1_result}, checking for Application Number...")
            # Check for saved Application Number - if found, retrieve application instead of stopping
            saved_app_number = get_saved_application_number()
            if saved_app_number:
                log_operation("fill_application_form", "INFO", f"Found Application Number: {saved_app_number}, retrieving application...")
                if retrieve_application(browser, wait, saved_app_number):
                    log_operation("fill_application_form", "SUCCESS", "Successfully retrieved application, re-starting form filling process...")
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "WARN", "Failed to retrieve application, trying restart_from_homepage...")
            # If no Application Number or retrieval failed, use restart_from_homepage
            log_operation("fill_application_form", "WARN", f"Page 1 returned: {page_1_result}, no Application Number or retrieval failed, trying restart_from_homepage...")
            if restart_from_homepage(browser, wait):
                log_operation("fill_application_form", "INFO", "Successfully restarted from homepage, re-starting form filling process...")
                # Recursively call fill_application_form to restart the entire process
                return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
            else:
                log_operation("fill_application_form", "ERROR", "Failed to restart from homepage, stopping form filling")
                return
        elif isinstance(page_1_result, str) and ("form_page_" in page_1_result or page_1_result == "same_page"):
            # Handle page jump or same page situation
            if "form_page_" in page_1_result:
                # Extract page number and continue from there
                page_num = int(str(page_1_result).split("_")[-1])
                log_operation("fill_application_form", "INFO", f"Page 1 redirected to form page {page_num}, continuing from there...")
            elif page_1_result == "same_page":
                # Still on same page, detect current page number
                log_operation("fill_application_form", "WARN", "Page 1 returned 'same_page', detecting current page...")
                page_num = detect_page_number_no_refresh(browser, wait)
                if page_num:
                    log_operation("fill_application_form", "INFO", f"Detected current page: {page_num}, continuing from there...")
                else:
                    log_operation("fill_application_form", "WARN", "Could not detect page number, assuming page 1 and continuing...")
                    page_num = 1
            
            if page_num and page_num >= 1:
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
                
                # Continue filling from the detected page
                current_page = page_num
                while current_page <= 9:
                    if current_page not in page_fill_functions:
                        break
                    
                    log_operation("fill_application_form", "INFO", f"Filling page {current_page}...")
                    time.sleep(2)
                    result = page_fill_functions[current_page](browser, wait)
                    
                    # Check for application error
                    if result == "application_error":
                        log_operation("fill_application_form", "ERROR", f"Application error detected on page {current_page} - stopping")
                        return
                    
                    # Check for homepage redirect
                    if result == "homepage_redirect" or (isinstance(result, str) and "homepage_redirect" in result):
                        if restart_from_homepage(browser, wait):
                            return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                        return
                    
                    # Check for page jump
                    if isinstance(result, str) and "form_page_" in result:
                        new_page_num = int(result.split("_")[-1])
                        log_operation("fill_application_form", "WARN", f"Page jump detected: from page {current_page} to page {new_page_num}")
                        current_page = new_page_num
                        continue
                    
                    # Check for same_page
                    if result == "same_page":
                        log_operation("fill_application_form", "WARN", f"Still on same page after filling page {current_page}, detecting current page...")
                        detected_page = detect_page_number_no_refresh(browser, wait)
                        if detected_page and detected_page != current_page:
                            log_operation("fill_application_form", "INFO", f"Detected page jump: from {current_page} to {detected_page}")
                            current_page = detected_page
                            continue
                    else:
                            log_operation("fill_application_form", "WARN", f"Could not detect page change, continuing from page {current_page + 1}")
                            current_page += 1
                            continue
                    
                    # If result is "success" or True, move to next page
                    if result == "success" or result == True:
                        current_page += 1
                        continue
                    
                    # If result is False or error, stop
                    if result == False or result == "error":
                        log_operation("fill_application_form", "WARN", f"Page {current_page} returned {result}, stopping")
                        return
                
                log_operation("fill_application_form", "SUCCESS", "Completed filling all pages")
                return
        
        # Wait a bit after page 1 navigation
        time.sleep(2)
        
        # Fill Page 2 and check result
        page_2_result = fill_page_2(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_2_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 2 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        # Check if error was resolved and we're on a different page, or same_page
        if isinstance(page_2_result, str) and ("form_page_" in str(page_2_result) or page_2_result == "same_page"):
            if "form_page_" in page_2_result:
                page_num = int(str(page_2_result).split("_")[-1])
                log_operation("fill_application_form", "INFO", f"Error resolved on Page 2, redirected to form page {page_num}, continuing from there...")
            elif page_2_result == "same_page":
                log_operation("fill_application_form", "WARN", "Page 2 returned 'same_page', detecting current page...")
                page_num = detect_page_number_no_refresh(browser, wait)
                if page_num:
                    log_operation("fill_application_form", "INFO", f"Detected current page: {page_num}, continuing from there...")
                else:
                    log_operation("fill_application_form", "WARN", "Could not detect page number, assuming page 2 and continuing...")
                    page_num = 2
            
            # Continue filling from the detected page
            if page_num and page_num >= 2:
                # Map page numbers to their fill functions
                page_fill_functions = {
                    2: fill_page_2,
                    3: fill_page_3,
                    4: fill_page_4,
                    5: fill_page_5,
                    6: fill_page_6,
                    7: fill_page_7,
                    8: fill_page_8,
                    9: fill_page_9,
                }
                
                # Continue filling from the detected page
                current_page = page_num
                while current_page <= 9:
                    if current_page not in page_fill_functions:
                        break
                    
                    log_operation("fill_application_form", "INFO", f"Filling page {current_page}...")
                    time.sleep(2)
                    result = page_fill_functions[current_page](browser, wait)
                    
                    # Check for application error
                    if result == "application_error":
                        log_operation("fill_application_form", "ERROR", f"Application error detected on page {current_page} - stopping")
                        return
                    
                    # Check for homepage redirect
                    if result == "homepage_redirect" or (isinstance(result, str) and "homepage_redirect" in result):
                        if restart_from_homepage(browser, wait):
                            return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                        return
                    
                    # Check for page jump
                    if isinstance(result, str) and "form_page_" in result:
                        new_page_num = int(result.split("_")[-1])
                        log_operation("fill_application_form", "WARN", f"Page jump detected: from page {current_page} to page {new_page_num}")
                        current_page = new_page_num
                        continue
                    
                    # Check for same_page
                    if result == "same_page":
                        log_operation("fill_application_form", "WARN", f"Still on same page after filling page {current_page}, detecting current page...")
                        detected_page = detect_page_number_no_refresh(browser, wait)
                        if detected_page and detected_page != current_page:
                            log_operation("fill_application_form", "INFO", f"Detected page jump: from {current_page} to {detected_page}")
                            current_page = detected_page
                            continue
                        else:
                            log_operation("fill_application_form", "WARN", f"Could not detect page change, continuing from page {current_page + 1}")
                            current_page += 1
                            continue
                    
                    # If result is "success" or True, move to next page
                    if result == "success" or result == True:
                        current_page += 1
                        continue
                    
                    # If result is False or error, stop
                    if result == False or result == "error":
                        log_operation("fill_application_form", "WARN", f"Page {current_page} returned {result}, stopping")
                        return
                
                log_operation("fill_application_form", "SUCCESS", "Completed filling all pages")
                return
        
        if page_2_result and ("homepage_redirect" in str(page_2_result) or "form_page_" in str(page_2_result)):
            log_operation("fill_application_form", "WARN", f"Page 2 returned: {page_2_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_2_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 2")
                    return
            elif "form_page_" in str(page_2_result):
                # Extract page number and continue from there
                page_num = int(str(page_2_result).split("_")[-1])
                log_operation("fill_application_form", "INFO", f"Redirected to form page {page_num}, continuing from there...")
                if page_num >= 3:
                    # Continue to page 3
                    time.sleep(2)
                    page_3_result = fill_page_3(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)
                    if page_3_result and ("homepage_redirect" in str(page_3_result) or "form_page_" in str(page_3_result)):
                        # Handle page 3 redirect
                        if "homepage_redirect" in str(page_3_result):
                            if restart_from_homepage(browser, wait):
                                return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                            return
                        elif "form_page_" in str(page_3_result):
                            page_num_3 = int(str(page_3_result).split("_")[-1])
                            if page_num_3 >= 4:
                                time.sleep(2)
                                fill_page_4(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)
                                return
                elif page_num >= 4:
                    # Skip to page 4
                    time.sleep(2)
                    fill_page_4(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)
                    return
        
        # Wait a bit after page 2 navigation
        time.sleep(2)
        
        # Fill Page 3
        page_3_result = fill_page_3(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_3_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 3 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_3_result and ("homepage_redirect" in str(page_3_result) or "form_page_" in str(page_3_result)):
            log_operation("fill_application_form", "WARN", f"Page 3 returned: {page_3_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_3_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 3")
                    return
            elif "form_page_" in str(page_3_result):
                # Extract page number and continue from there
                page_num = int(str(page_3_result).split("_")[-1])
                log_operation("fill_application_form", "INFO", f"Redirected to form page {page_num}, continuing from there...")
                if page_num >= 4:
                    # Skip to page 4
                    time.sleep(2)
                    fill_page_4(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)
                    return

        # Wait a bit after page 3 navigation
        time.sleep(2)
        
        # Fill Page 4
        page_4_result = fill_page_4(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_4_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 4 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_4_result and ("homepage_redirect" in str(page_4_result) or "form_page_" in str(page_4_result)):
            log_operation("fill_application_form", "WARN", f"Page 4 returned: {page_4_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_4_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 4")
                    return
        
        # Wait a bit after page 4 navigation
        time.sleep(2)
        
        # Fill Page 5
        page_5_result = fill_page_5(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_5_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 5 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_5_result and ("homepage_redirect" in str(page_5_result) or "form_page_" in str(page_5_result)):
            log_operation("fill_application_form", "WARN", f"Page 5 returned: {page_5_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_5_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 5")
                    return
        
        # Wait a bit after page 5 navigation
        time.sleep(2)
        
        # Fill Page 6
        page_6_result = fill_page_6(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_6_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 6 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_6_result and ("homepage_redirect" in str(page_6_result) or "form_page_" in str(page_6_result)):
            log_operation("fill_application_form", "WARN", f"Page 6 returned: {page_6_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_6_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 6")
                    return
        
        # Wait a bit after page 6 navigation
        time.sleep(2)
        
        # Fill Page 7
        page_7_result = fill_page_7(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_7_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 7 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_7_result and ("homepage_redirect" in str(page_7_result) or "form_page_" in str(page_7_result)):
            log_operation("fill_application_form", "WARN", f"Page 7 returned: {page_7_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_7_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 7")
                    return
        
        # Wait a bit after page 7 navigation
        time.sleep(2)
        
        # Fill Page 8
        page_8_result = fill_page_8(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_8_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 8 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_8_result and ("homepage_redirect" in str(page_8_result) or "form_page_" in str(page_8_result)):
            log_operation("fill_application_form", "WARN", f"Page 8 returned: {page_8_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_8_result):
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 8")
                    return
        
        # Wait a bit after page 8 navigation
        time.sleep(2)
        
        # Fill Page 9
        page_9_result = fill_page_9(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_9_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 9 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        if page_9_result and ("homepage_redirect" in str(page_9_result) or "form_page_" in str(page_9_result)):
            log_operation("fill_application_form", "WARN", f"Page 9 returned: {page_9_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_9_result):
                # Check for saved Application Number - if found, retrieve application instead of clicking Continue
                saved_app_number = get_saved_application_number()
                if saved_app_number:
                    log_operation("fill_application_form", "INFO", f"Found Application Number: {saved_app_number}, retrieving application...")
                    if retrieve_application(browser, wait, saved_app_number):
                        log_operation("fill_application_form", "SUCCESS", "Successfully retrieved application, re-starting form filling process...")
                        return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                    else:
                        log_operation("fill_application_form", "WARN", "Failed to retrieve application, trying restart_from_homepage...")
                # If no Application Number or retrieval failed, use restart_from_homepage
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 9")
                    return
            elif "form_page_" in str(page_9_result):
                # Extract page number and continue from there
                page_num = int(str(page_9_result).split("_")[-1])
                log_operation("fill_application_form", "INFO", f"Page 9 redirected to form page {page_num}, continuing from there...")
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
                if page_num in page_fill_functions:
                    time.sleep(2)
                    result = page_fill_functions[page_num](browser, wait)
                    # Check for application error
                    if result == "application_error":
                        log_operation("fill_application_form", "ERROR", f"Application error detected on page {page_num} - stopping")
                        return
                    # Handle submission_complete
                    if result == "submission_complete":
                        log_operation("fill_application_form", "SUCCESS", "Application submission completed successfully!")
                        print("\n[SUCCESS] Application has been submitted successfully!")
                        return
                    # Handle other results if needed
                    return
        
        # Wait a bit after page 9 navigation
        time.sleep(2)
        
        # Fill Page 10
        page_10_result = fill_page_10(browser, wait, screenshots_dir=screenshots_dir if enable_screenshots else None)

        # Check for application error - stop all page filling immediately
        if page_10_result == "application_error":
            log_operation("fill_application_form", "ERROR", "Application error detected on Page 10 - stopping all page filling immediately!")
            print("\n[CRITICAL ERROR] Application error detected - all page filling operations stopped!")
            return
        
        # Check if submission is complete
        if page_10_result == "submission_complete":
            log_operation("fill_application_form", "SUCCESS", "Application submission completed successfully!")
            print("\n[SUCCESS] Application has been submitted successfully!")
            print("[INFO] Thank you page HTML has been saved. Page will remain on thank you page.")
            return
        
        if page_10_result and ("homepage_redirect" in str(page_10_result) or "form_page_" in str(page_10_result)):
            log_operation("fill_application_form", "WARN", f"Page 10 returned: {page_10_result}, stopping all page filling and handling redirect...")
            if "homepage_redirect" in str(page_10_result):
                # Check for saved Application Number - if found, retrieve application instead of clicking Continue
                saved_app_number = get_saved_application_number()
                if saved_app_number:
                    log_operation("fill_application_form", "INFO", f"Found Application Number: {saved_app_number}, retrieving application...")
                    if retrieve_application(browser, wait, saved_app_number):
                        log_operation("fill_application_form", "SUCCESS", "Successfully retrieved application, re-starting form filling process...")
                        return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                    else:
                        log_operation("fill_application_form", "WARN", "Failed to retrieve application, trying restart_from_homepage...")
                # If no Application Number or retrieval failed, use restart_from_homepage
                if restart_from_homepage(browser, wait):
                    return fill_application_form(browser, wait, enable_screenshots, screenshots_dir)
                else:
                    log_operation("fill_application_form", "ERROR", "Failed to restart from homepage after page 10")
                    return
        
        print("\n[SUCCESS] Form filling process completed")
        
        # Note: Application Number extraction is now done in fill_page_4 and fill_page_5
        # No need to check again here as it should have been saved already
        
    except Exception as e:
        print(f"[ERROR] Error during form filling: {e}")
        import traceback
        traceback.print_exc()


