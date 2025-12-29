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
    log_operation
)

def fill_dropdown_by_label(browser, wait, label_text, value):
    """
    Fill a dropdown/select element by finding its label
    
    Args:
        browser: WebDriver instance
        wait: WebDriverWait instance
        label_text: Text of the label (partial match)
        value: Value to select from dropdown
    """
    try:
        print(f"[INFO] Filling dropdown: {label_text} = {value}")
        
        # Increase wait time for this operation
        extended_wait = WebDriverWait(browser, 15)
        
        # Try multiple ways to find the label
        label = None
        label_selectors = [
            f"//label[contains(text(), '{label_text}')]",
            f"//label[contains(., '{label_text}')]",
            f"//*[contains(text(), '{label_text}') and (self::label or self::span or self::div)]",
        ]
        
        for selector in label_selectors:
            try:
                label = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                print(f"[SUCCESS] Found label using: {selector}")
                break
            except TimeoutException:
                continue
        
        if not label:
            print(f"[WARN] Could not find label containing '{label_text}'")
            return
        
        # Get the for attribute to find associated select element
        select_element = None
        label_for = label.get_attribute("for")
        
        if label_for:
            try:
                select_element = browser.find_element(By.ID, label_for)
                print(f"[SUCCESS] Found select by label 'for' attribute: {label_for}")
            except:
                pass
        
        # If not found, try other methods
        if not select_element:
            try:
                # Find select near the label
                select_element = label.find_element(By.XPATH, ".//following::select[1]")
            except:
                try:
                    select_element = label.find_element(By.XPATH, ".//preceding::select[1]")
                except:
                    try:
                        # Find select in the same container
                        container = label.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form][1]")
                        select_element = container.find_element(By.XPATH, ".//select[1]")
                    except:
                        pass
        
        if not select_element:
            print(f"[WARN] Could not find select element for '{label_text}'")
            return
        
        # Scroll to element
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
        time.sleep(0.5)
        
        # Wait for select to be clickable
        extended_wait.until(EC.element_to_be_clickable(select_element))
        
        # Select the value
        select = Select(select_element)
        selected = False
        
        # Check if dropdown has PostBack behavior
        select_id = select_element.get_attribute("id")
        has_postback = browser.execute_script("""
            var select = arguments[0];
            return select.onchange !== null || select.getAttribute('onchange') !== null;
        """, select_element)
        
        # Record current URL if PostBack is expected
        current_url = None
        if has_postback:
            current_url = browser.current_url
            print(f"[INFO] Dropdown has PostBack behavior, current URL: {current_url}")
        
        # Try by visible text
        try:
            select.select_by_visible_text(value)
            print(f"[SUCCESS] Selected '{value}' in '{label_text}'")
            selected = True
        except:
            pass
        
        if not selected:
            # Try by value attribute
            try:
                select.select_by_value(value)
                print(f"[SUCCESS] Selected '{value}' in '{label_text}' (by value)")
                selected = True
            except:
                pass
        
        if not selected:
            # Try partial match
            options = select.options
            for option in options:
                option_text = option.text.strip()
                if value.lower() in option_text.lower() or option_text.lower() in value.lower():
                    select.select_by_visible_text(option_text)
                    print(f"[SUCCESS] Selected '{option_text}' in '{label_text}' (partial match)")
                    selected = True
                    break
        
        if not selected:
            print(f"[WARN] Could not select '{value}' in dropdown '{label_text}'")
            # Print available options for debugging
            try:
                options = select.options
                print(f"[DEBUG] Available options: {[opt.text for opt in options[:5]]}")
            except:
                pass
            return
        
        # Wait for PostBack if it was triggered
        if has_postback and selected:
            print("[INFO] Waiting for PostBack to complete...")
            try:
                # Wait for page to start refreshing
                time.sleep(1)
                
                # Wait for document ready state
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                
                # Wait for the select element to be present again (page reloaded)
                if select_id:
                    try:
                        extended_wait.until(EC.presence_of_element_located((By.ID, select_id)))
                    except:
                        # If element not found by ID, try to find it again by label
                        extended_wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{label_text}')]")))
                
                # Verify we're still on the form page
                new_url = browser.current_url
                print(f"[INFO] URL after PostBack: {new_url}")
                
                if current_url and "VisaTypeDetails.aspx" not in new_url and "OnlineHome.aspx" in new_url:
                    print("[WARN] Page redirected to homepage after PostBack!")
                    print("[INFO] This might be due to form validation or session timeout")
                    return
                
                # Additional wait for dynamic content
                time.sleep(2)
                print("[SUCCESS] PostBack completed successfully")
            except TimeoutException:
                print("[WARN] Initial PostBack wait timeout in fill_dropdown_by_label, continuing to wait until PostBack completes...")
                # Wait indefinitely until PostBack completes or page redirects
                postback_completed = False
                check_count = 0
                
                while not postback_completed:
                    try:
                        check_count += 1
                        if check_count % 10 == 0:  # Print status every 10 seconds
                            print(f"[INFO] Still waiting for dropdown PostBack to complete... (checked {check_count} times)")
                        
                        # Check document ready state
                        ready_state = browser.execute_script("return document.readyState")
                        current_url_check = browser.current_url
                        
                        # If redirected to homepage, restart from homepage
                        if "OnlineHome.aspx" in current_url_check:
                            log_operation("fill_dropdown_by_label", "WARN", "Page redirected to homepage during dropdown PostBack wait - restarting from homepage")
                            # Restart from homepage instead of continuing form filling
                            if restart_from_homepage(browser, wait):
                                log_operation("fill_dropdown_by_label", "INFO", "Successfully restarted from homepage, stopping form filling to restart process")
                                return
                            else:
                                log_operation("fill_dropdown_by_label", "ERROR", "Failed to restart from homepage, stopping form filling")
                                return
                        
                        # Check if we're still on form page
                        if "VisaTypeDetails.aspx" in current_url_check:
                            # Check if key element is present (try to find the select element again)
                            try:
                                if select_id:
                                    select_found = browser.find_elements(By.ID, select_id)
                                    if ready_state == "complete" and select_found:
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
                print(f"[WARN] Error waiting for PostBack: {e}")
                # Check page state before continuing
                try:
                    current_url_check = browser.current_url
                    if "OnlineHome.aspx" in current_url_check:
                        print("[ERROR] Page redirected to homepage - stopping form filling")
                        return
                except:
                    pass
                time.sleep(2)
        elif selected:
            # Short wait if no PostBack
            time.sleep(0.5)
        
    except Exception as e:
        print(f"[WARN] Could not fill dropdown '{label_text}': {str(e)[:200]}")



def select_radio_by_label(browser, wait, label_text, value, alternative_values=None):
    """
    Select a radio button by finding its label
    
    Args:
        browser: WebDriver instance
        wait: WebDriverWait instance
        label_text: Text of the label (partial match)
        value: Value/text of the radio option to select
        alternative_values: List of alternative values to try if main value fails
    """
    if alternative_values is None:
        alternative_values = []
    try:
        print(f"[INFO] Selecting radio: {label_text} = {value}")
        
        # Increase wait time
        extended_wait = WebDriverWait(browser, 15)
        
        # Find the fieldset or container with the label - be more specific
        # Try to find the exact question/fieldset first
        container = None
        
        # Try multiple strategies: full text, partial text, and key words
        # Strategy 1: Try full text match
        container_selectors = [
            f"//label[contains(text(), '{label_text}')]",
            f"//span[contains(text(), '{label_text}')]",
            f"//td[contains(text(), '{label_text}')]",
            f"//div[contains(text(), '{label_text}')]",
            f"//*[contains(text(), '{label_text}')]",
        ]
        
        for selector in container_selectors:
            try:
                containers = browser.find_elements(By.XPATH, selector)
                # Find the container that is closest to radio buttons
                for cont in containers:
                    try:
                        # Check if this container has radio buttons nearby
                        parent = cont.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form or self::tr or self::td][1]")
                        nearby_radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
                        if nearby_radios:
                            container = cont
                            print(f"[DEBUG] Found container with {len(nearby_radios)} nearby radio buttons using full text match")
                            break
                    except:
                        continue
                if container:
                    break
            except:
                continue
        
        # Strategy 2: If full text match fails, try partial text match (first 30 characters)
        if not container and len(label_text) > 30:
            partial_text = label_text[:30]
            print(f"[DEBUG] Trying partial text match: '{partial_text}'")
            partial_selectors = [
                f"//label[contains(text(), '{partial_text}')]",
                f"//span[contains(text(), '{partial_text}')]",
                f"//td[contains(text(), '{partial_text}')]",
                f"//div[contains(text(), '{partial_text}')]",
                f"//*[contains(text(), '{partial_text}')]",
            ]
            
            for selector in partial_selectors:
                try:
                    containers = browser.find_elements(By.XPATH, selector)
                    for cont in containers:
                        try:
                            parent = cont.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form or self::tr or self::td][1]")
                            nearby_radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
                            if nearby_radios:
                                container = cont
                                print(f"[DEBUG] Found container with {len(nearby_radios)} nearby radio buttons using partial text match")
                                break
                        except:
                            continue
                    if container:
                        break
                except:
                    continue
        
        # Strategy 3: If still not found, try key words (extract important words)
        if not container:
            # Extract key words from label_text (words longer than 4 characters)
            import re
            words = re.findall(r'\b\w{5,}\b', label_text.lower())
            if words:
                print(f"[DEBUG] Trying key words match: {words[:3]}")  # Use first 3 key words
                for word in words[:3]:
                    key_word_selectors = [
                        f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                        f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                        f"//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                    ]
                    
                    for selector in key_word_selectors:
                        try:
                            containers = browser.find_elements(By.XPATH, selector)
                            for cont in containers:
                                try:
                                    # Verify the container text contains multiple key words
                                    cont_text = cont.text.lower()
                                    matching_words = sum(1 for w in words[:3] if w in cont_text)
                                    if matching_words >= 2:  # At least 2 key words match
                                        parent = cont.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form or self::tr or self::td][1]")
                                        nearby_radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
                                        if nearby_radios:
                                            container = cont
                                            print(f"[DEBUG] Found container with {len(nearby_radios)} nearby radio buttons using key words match")
                                            break
                                except:
                                    continue
                            if container:
                                break
                        except:
                            continue
                    if container:
                        break
        
        if not container:
            print(f"[WARN] Could not find container with text '{label_text}'")
            # Print debug information: search for similar text on page
            try:
                page_text = browser.find_element(By.TAG_NAME, "body").text
                # Look for similar text patterns
                similar_patterns = [
                    "travelling",
                    "other person",
                    "business colleague",
                    "family member",
                    "group"
                ]
                found_patterns = [p for p in similar_patterns if p.lower() in page_text.lower()]
                if found_patterns:
                    print(f"[DEBUG] Found similar patterns on page: {found_patterns}")
                    # Try to find elements containing these patterns
                    for pattern in found_patterns[:2]:  # Try first 2 patterns
                        try:
                            similar_elements = browser.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]")
                            if similar_elements:
                                print(f"[DEBUG] Found {len(similar_elements)} elements containing '{pattern}'")
                                for elem in similar_elements[:3]:  # Show first 3
                                    try:
                                        elem_text = elem.text.strip()[:100]
                                        if elem_text:
                                            print(f"[DEBUG]   - Element text: {elem_text}")
                                    except:
                                        pass
                        except:
                            pass
            except Exception as e:
                print(f"[DEBUG] Error searching for similar text: {e}")
            return
        
        # Find radio buttons in the same group as this question
        # Radio buttons in the same group share the same 'name' attribute
        try:
            parent = container.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form or self::tr or self::td][1]")
            # First, try to find the radio button group by name attribute
            # Look for radio buttons that are siblings or in the same container
            all_radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
            
            if not all_radios:
                print(f"[WARN] No radio buttons found near '{label_text}'")
                return
            
            print(f"[DEBUG] Found {len(all_radios)} radio buttons near '{label_text}'")
            
            # Group radios by name attribute to find the correct group
            radio_groups = {}
            for radio in all_radios:
                radio_name = radio.get_attribute("name")
                if radio_name:
                    if radio_name not in radio_groups:
                        radio_groups[radio_name] = []
                    radio_groups[radio_name].append(radio)
            
            # If we have multiple groups, try to find the one closest to our label
            # Otherwise, use the first group
            radios = None
            if len(radio_groups) > 1:
                print(f"[DEBUG] Found {len(radio_groups)} radio button groups, trying to find the correct one...")
                # Try to find the group that is closest to the label
                for group_name, group_radios in radio_groups.items():
                    # Check if any radio in this group is near our container
                    for radio in group_radios:
                        try:
                            # Check if radio is in the same row or nearby element as container
                            radio_parent = radio.find_element(By.XPATH, "./ancestor::*[self::tr or self::td or self::div][1]")
                            container_parent = container.find_element(By.XPATH, "./ancestor::*[self::tr or self::td or self::div][1]")
                            if radio_parent == container_parent or radio_parent.text == container_parent.text:
                                radios = group_radios
                                print(f"[DEBUG] Selected radio group '{group_name}' with {len(radios)} buttons")
                                break
                        except:
                            continue
                    if radios:
                        break
                
                # If still not found, use the group with the most buttons (likely the correct one)
                if not radios:
                    largest_group = max(radio_groups.items(), key=lambda x: len(x[1]))
                    radios = largest_group[1]
                    print(f"[DEBUG] Using largest radio group '{largest_group[0]}' with {len(radios)} buttons")
            else:
                # Only one group, use it
                radios = list(radio_groups.values())[0] if radio_groups else all_radios
                print(f"[DEBUG] Using single radio group with {len(radios)} buttons")
        except Exception as e:
            print(f"[DEBUG] Error finding radio group: {e}")
            # Fallback: try to find radios directly
            try:
                parent = container.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form][1]")
                radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
                print(f"[DEBUG] Fallback: Found {len(radios)} radio buttons")
            except:
                radios = []
        
        if not radios:
            print(f"[WARN] No radio buttons found for '{label_text}'")
            return
        
        radio_selected = False
        for radio in radios:
            try:
                # Get associated label
                radio_id = radio.get_attribute("id")
                if radio_id:
                    try:
                        radio_label = browser.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                        label_text_content = radio_label.text.strip()
                        
                        # Try main value
                        values_to_try = [value] + alternative_values
                        for val in values_to_try:
                            if val.lower() in label_text_content.lower() or label_text_content.lower() in val.lower():
                                # CRITICAL: Re-locate element before clicking to avoid StaleElementReferenceException
                                try:
                                    # Re-find the radio button by ID to get a fresh reference
                                    radio_id_fresh = radio_id
                                    radio_fresh = extended_wait.until(EC.element_to_be_clickable((By.ID, radio_id_fresh)))
                                    
                                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_fresh)
                                    time.sleep(0.5)
                                    
                                    # Try multiple click methods
                                    clicked = False
                                    if not radio_fresh.is_selected():
                                        try:
                                            # Method 1: Standard click
                                            radio_fresh.click()
                                            time.sleep(0.3)
                                            # Re-verify by re-finding element
                                            radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                            if radio_fresh.is_selected():
                                                clicked = True
                                                print(f"[SUCCESS] Selected radio '{label_text_content}' for '{label_text}' (standard click)")
                                            else:
                                                # Method 2: JavaScript click
                                                browser.execute_script("arguments[0].click();", radio_fresh)
                                                time.sleep(0.3)
                                                radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                if radio_fresh.is_selected():
                                                    clicked = True
                                                    print(f"[SUCCESS] Selected radio '{label_text_content}' for '{label_text}' (JavaScript click)")
                                                else:
                                                    # Method 3: Set checked property directly
                                                    browser.execute_script("arguments[0].checked = true;", radio_fresh)
                                                    # Trigger change event if exists
                                                    browser.execute_script("if(arguments[0].onchange) arguments[0].onchange();", radio_fresh)
                                                    time.sleep(0.3)
                                                    radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                    if radio_fresh.is_selected():
                                                        clicked = True
                                                        print(f"[SUCCESS] Selected radio '{label_text_content}' for '{label_text}' (direct property set)")
                                        except Exception as click_error:
                                            print(f"[DEBUG] Click error: {click_error}")
                                            # Try one more time with fresh element
                                            try:
                                                radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                browser.execute_script("arguments[0].checked = true; arguments[0].click();", radio_fresh)
                                                time.sleep(0.3)
                                                radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                if radio_fresh.is_selected():
                                                    clicked = True
                                                    print(f"[SUCCESS] Selected radio '{label_text_content}' for '{label_text}' (retry with fresh element)")
                                            except:
                                                pass
                                except Exception as stale_error:
                                    print(f"[DEBUG] Stale element error, trying to re-locate: {stale_error}")
                                    # Try to re-find the radio button
                                    try:
                                        radio_fresh = extended_wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
                                        browser.execute_script("arguments[0].checked = true; arguments[0].click();", radio_fresh)
                                        time.sleep(0.3)
                                        radio_fresh = browser.find_element(By.ID, radio_id)
                                        clicked = radio_fresh.is_selected()
                                        if clicked:
                                            print(f"[SUCCESS] Selected radio '{label_text_content}' for '{label_text}' (re-located after stale)")
                                    except:
                                        print(f"[DEBUG] Could not re-locate radio button")
                                        clicked = False
                                
                                # Check if clicked (use fresh element reference)
                                try:
                                    radio_check = browser.find_element(By.ID, radio_id)
                                    if clicked or radio_check.is_selected():
                                        radio_selected = True
                                        # Additional verification: re-find element to ensure it's selected
                                        try:
                                            time.sleep(0.2)
                                            verify_radio = browser.find_element(By.ID, radio_id)
                                            if verify_radio.is_selected():
                                                print(f"[SUCCESS] Verified radio selection for '{label_text}'")
                                            else:
                                                print(f"[WARN] Radio selection not verified, but continuing...")
                                        except:
                                            pass
                                        break
                                except:
                                    if clicked:
                                        radio_selected = True
                                        break
                        
                        if radio_selected:
                            break
                    except:
                        pass
                        
                        # Also check value attribute
                        radio_value = radio.get_attribute("value")
                        if radio_value:
                            values_to_try = [value] + alternative_values
                            for val in values_to_try:
                                if val.lower() in radio_value.lower() or radio_value.lower() in val.lower():
                                    # CRITICAL: Re-locate element before clicking to avoid StaleElementReferenceException
                                    try:
                                        radio_id_fresh = radio_id
                                        radio_fresh = extended_wait.until(EC.element_to_be_clickable((By.ID, radio_id_fresh)))
                                        
                                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_fresh)
                                        time.sleep(0.5)
                                        
                                        # Try multiple click methods
                                        clicked = False
                                        if not radio_fresh.is_selected():
                                            try:
                                                # Method 1: Standard click
                                                radio_fresh.click()
                                                time.sleep(0.3)
                                                # Re-verify by re-finding element
                                                radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                if radio_fresh.is_selected():
                                                    clicked = True
                                                    print(f"[SUCCESS] Selected radio by value '{radio_value}' for '{label_text}' (standard click)")
                                                else:
                                                    # Method 2: JavaScript click
                                                    browser.execute_script("arguments[0].click();", radio_fresh)
                                                    time.sleep(0.3)
                                                    radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                    if radio_fresh.is_selected():
                                                        clicked = True
                                                        print(f"[SUCCESS] Selected radio by value '{radio_value}' for '{label_text}' (JavaScript click)")
                                                    else:
                                                        # Method 3: Set checked property directly
                                                        browser.execute_script("arguments[0].checked = true;", radio_fresh)
                                                        browser.execute_script("if(arguments[0].onchange) arguments[0].onchange();", radio_fresh)
                                                        time.sleep(0.3)
                                                        radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                        if radio_fresh.is_selected():
                                                            clicked = True
                                                            print(f"[SUCCESS] Selected radio by value '{radio_value}' for '{label_text}' (direct property set)")
                                            except Exception as click_error:
                                                print(f"[DEBUG] Click error: {click_error}")
                                                # Try one more time with fresh element
                                                try:
                                                    radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                    browser.execute_script("arguments[0].checked = true; arguments[0].click();", radio_fresh)
                                                    time.sleep(0.3)
                                                    radio_fresh = browser.find_element(By.ID, radio_id_fresh)
                                                    if radio_fresh.is_selected():
                                                        clicked = True
                                                        print(f"[SUCCESS] Selected radio by value '{radio_value}' for '{label_text}' (retry with fresh element)")
                                                except:
                                                    pass
                                    except Exception as stale_error:
                                        print(f"[DEBUG] Stale element error, trying to re-locate: {stale_error}")
                                        try:
                                            radio_fresh = extended_wait.until(EC.element_to_be_clickable((By.ID, radio_id)))
                                            browser.execute_script("arguments[0].checked = true; arguments[0].click();", radio_fresh)
                                            time.sleep(0.3)
                                            radio_fresh = browser.find_element(By.ID, radio_id)
                                            clicked = radio_fresh.is_selected()
                                            if clicked:
                                                print(f"[SUCCESS] Selected radio by value '{radio_value}' for '{label_text}' (re-located after stale)")
                                        except:
                                            clicked = False
                                    
                                    # Check if clicked (use fresh element reference)
                                    try:
                                        radio_check = browser.find_element(By.ID, radio_id)
                                        if clicked or radio_check.is_selected():
                                            radio_selected = True
                                            break
                                    except:
                                        if clicked:
                                            radio_selected = True
                                            break
                                        # Additional verification: re-find element to ensure it's selected
                                        try:
                                            time.sleep(0.2)
                                            radio_id = radio.get_attribute("id")
                                            if radio_id:
                                                verify_radio = browser.find_element(By.ID, radio_id)
                                                if verify_radio.is_selected():
                                                    print(f"[SUCCESS] Verified radio selection by value for '{label_text}'")
                                                else:
                                                    print(f"[WARN] Radio selection not verified, but continuing...")
                                        except:
                                            pass
                                        break
                            
                            if radio_selected:
                                break
            except Exception as e:
                continue
            
            if radio_selected:
                break
        
        if not radio_selected:
            print(f"[WARN] Could not find radio button for '{label_text}' with value '{value}'")
            # Print available radio options for debugging
            try:
                containers = browser.find_elements(By.XPATH, f"//*[contains(text(), '{label_text}')]")
                if containers:
                    parent = containers[0].find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form][1]")
                    radios = parent.find_elements(By.XPATH, ".//input[@type='radio']")
                    print(f"[DEBUG] Available radio options:")
                    for radio in radios[:5]:  # Show first 5
                        try:
                            radio_id = radio.get_attribute("id")
                            if radio_id:
                                radio_label = browser.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                                print(f"  - {radio_label.text.strip()}")
                        except:
                            pass
            except:
                pass
            
    except Exception as e:
        print(f"[WARN] Could not select radio '{label_text}': {str(e)[:200]}")



def fill_text_by_label(browser, wait, label_text, value):
    """
    Fill a text input field by finding its label
    
    Args:
        browser: WebDriver instance
        wait: WebDriverWait instance
        label_text: Text of the label (partial match)
        value: Text value to fill
    """
    try:
        print(f"[INFO] Filling text field: {label_text} = {value}")
        
        # Increase wait time
        extended_wait = WebDriverWait(browser, 15)
        
        # Strategy 1: Try direct ID/name matching first (for common field names)
        # Extract key words from label_text to build potential field IDs
        label_lower = label_text.lower()
        potential_ids = []
        if "phone" in label_lower:
            potential_ids.extend(["Phone", "phone", "ContactPhone", "contactPhone", "txtPhone", "txtContactPhone"])
        if "email" in label_lower:
            potential_ids.extend(["Email", "email", "ContactEmail", "contactEmail", "txtEmail", "txtContactEmail"])
        if "address" in label_lower:
            potential_ids.extend(["Address", "address", "AddressLine", "addressLine", "txtAddress"])
        
        input_element = None
        for potential_id in potential_ids:
            # Try by ID
            try:
                input_element = browser.find_element(By.XPATH, f"//input[contains(@id, '{potential_id}') or contains(@name, '{potential_id}')]")
                print(f"[SUCCESS] Found input by potential ID/name: {potential_id}")
                break
            except:
                continue
        
        # Strategy 2: Try to find the label
        label = None
        if not input_element:
            label_selectors = [
                f"//label[contains(text(), '{label_text}')]",
                f"//label[contains(., '{label_text}')]",
                f"//span[contains(text(), '{label_text}')]",
                f"//td[contains(text(), '{label_text}')]",
                f"//div[contains(text(), '{label_text}')]",
                f"//*[contains(text(), '{label_text}') and (self::label or self::span or self::div or self::td)]",
            ]
            
            for selector in label_selectors:
                try:
                    labels = browser.find_elements(By.XPATH, selector)
                    if labels:
                        # Find the label that is closest to an input field
                        for lbl in labels:
                            try:
                                # Check if there's an input nearby
                                nearby_inputs = lbl.find_elements(By.XPATH, ".//following::input[1] | .//preceding::input[1] | ./ancestor::*[self::tr or self::td]//input[1]")
                                if nearby_inputs:
                                    label = lbl
                                    print(f"[SUCCESS] Found label using: {selector}")
                                    break
                            except:
                                continue
                        if label:
                            break
                except:
                    continue
            
            # Strategy 3: If full text match fails, try partial text match
            if not label and len(label_text) > 10:
                partial_text = label_text[:20]  # First 20 characters
                print(f"[DEBUG] Trying partial text match: '{partial_text}'")
                partial_selectors = [
                    f"//label[contains(text(), '{partial_text}')]",
                    f"//span[contains(text(), '{partial_text}')]",
                    f"//td[contains(text(), '{partial_text}')]",
                    f"//*[contains(text(), '{partial_text}')]",
                ]
                
                for selector in partial_selectors:
                    try:
                        labels = browser.find_elements(By.XPATH, selector)
                        if labels:
                            for lbl in labels:
                                try:
                                    nearby_inputs = lbl.find_elements(By.XPATH, ".//following::input[1] | .//preceding::input[1]")
                                    if nearby_inputs:
                                        label = lbl
                                        print(f"[SUCCESS] Found label using partial text match: {selector}")
                                        break
                                except:
                                    continue
                            if label:
                                break
                    except:
                        continue
            
            # Strategy 4: Try key words matching
            if not label:
                import re
                words = re.findall(r'\b\w{4,}\b', label_text.lower())
                if words:
                    print(f"[DEBUG] Trying key words match: {words[:3]}")
                    for word in words[:3]:
                        key_word_selectors = [
                            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                            f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                            f"//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{word}')]",
                        ]
                        
                        for selector in key_word_selectors:
                            try:
                                labels = browser.find_elements(By.XPATH, selector)
                                if labels:
                                    for lbl in labels:
                                        try:
                                            lbl_text = lbl.text.lower()
                                            matching_words = sum(1 for w in words[:3] if w in lbl_text)
                                            if matching_words >= 2:  # At least 2 key words match
                                                nearby_inputs = lbl.find_elements(By.XPATH, ".//following::input[1] | .//preceding::input[1]")
                                                if nearby_inputs:
                                                    label = lbl
                                                    print(f"[SUCCESS] Found label using key words match")
                                                    break
                                        except:
                                            continue
                                    if label:
                                        break
                            except:
                                continue
                        if label:
                            break
        
        if not label and not input_element:
            print(f"[WARN] Could not find label containing '{label_text}'")
            # Print debug information: search for similar text on page
            try:
                page_text = browser.find_element(By.TAG_NAME, "body").text
                # Look for similar text patterns
                similar_patterns = []
                if "phone" in label_text.lower():
                    similar_patterns.extend(["phone", "contact", "telephone"])
                if "email" in label_text.lower():
                    similar_patterns.extend(["email", "e-mail", "contact"])
                if "address" in label_text.lower():
                    similar_patterns.extend(["address", "street", "location"])
                
                found_patterns = [p for p in similar_patterns if p.lower() in page_text.lower()]
                if found_patterns:
                    print(f"[DEBUG] Found similar patterns on page: {found_patterns}")
                    # Try to find elements containing these patterns
                    for pattern in found_patterns[:2]:
                        try:
                            similar_elements = browser.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]")
                            if similar_elements:
                                print(f"[DEBUG] Found {len(similar_elements)} elements containing '{pattern}'")
                                for elem in similar_elements[:3]:
                                    try:
                                        elem_text = elem.text.strip()[:100]
                                        if elem_text:
                                            print(f"[DEBUG]   - Element text: {elem_text}")
                                    except:
                                        pass
                        except:
                            pass
            except Exception as e:
                print(f"[DEBUG] Error searching for similar text: {e}")
            return
        
        # Get the for attribute to find associated input (if we found label)
        if label and not input_element:
            label_for = label.get_attribute("for")
            
            if label_for:
                try:
                    input_element = extended_wait.until(EC.presence_of_element_located((By.ID, label_for)))
                    print(f"[SUCCESS] Found input by label 'for' attribute: {label_for}")
                except:
                    pass
            
            # If not found, try other methods
            if not input_element:
                try:
                    # Try following sibling input
                    input_element = label.find_element(By.XPATH, ".//following::input[@type='text' or @type='' or not(@type)][1]")
                    print(f"[SUCCESS] Found input following label")
                except:
                    try:
                        # Try preceding sibling input
                        input_element = label.find_element(By.XPATH, ".//preceding::input[@type='text' or @type='' or not(@type)][1]")
                        print(f"[SUCCESS] Found input preceding label")
                    except:
                        try:
                            # Find input in the same row (for table layouts)
                            parent_row = label.find_element(By.XPATH, "./ancestor::tr[1]")
                            input_element = parent_row.find_element(By.XPATH, ".//input[@type='text' or @type='' or not(@type)][1]")
                            print(f"[SUCCESS] Found input in same table row as label")
                        except:
                            try:
                                # Find input in the same container
                                container = label.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form or self::td][1]")
                                input_element = container.find_element(By.XPATH, ".//input[@type='text' or @type='' or not(@type)][1]")
                                print(f"[SUCCESS] Found input in same container as label")
                            except:
                                pass
        
        if not input_element:
            print(f"[WARN] Could not find input element for '{label_text}'")
            return
        
        # Scroll to element
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
        time.sleep(0.5)
        
        # Wait for input to be clickable
        extended_wait.until(EC.element_to_be_clickable(input_element))
        
        # Clear and fill
        input_element.clear()
        time.sleep(0.2)
        input_element.send_keys(value)
        time.sleep(0.2)
        print(f"[SUCCESS] Filled '{value}' in '{label_text}'")
        
    except Exception as e:
        print(f"[WARN] Could not fill text field '{label_text}': {str(e)[:200]}")



def fill_date_by_label(browser, wait, label_text, date_type, date_value):
    """
    Fill a date field by finding its label
    
    Args:
        browser: WebDriver instance
        wait: WebDriverWait instance
        label_text: Text of the label (partial match)
        date_type: "From" or "To"
        date_value: Date value in format "DD/MM/YYYY"
    """
    try:
        print(f"[INFO] Filling date field: {label_text} - {date_type} = {date_value}")
        
        # Increase wait time
        extended_wait = WebDriverWait(browser, 15)
        
        # Try multiple ways to find the label
        label = None
        label_selectors = [
            f"//label[contains(text(), '{label_text}')]",
            f"//label[contains(., '{label_text}')]",
            f"//*[contains(text(), '{label_text}') and (self::label or self::span or self::div)]",
        ]
        
        for selector in label_selectors:
            try:
                label = extended_wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                print(f"[SUCCESS] Found label using: {selector}")
                break
            except TimeoutException:
                continue
        
        if not label:
            print(f"[WARN] Could not find label containing '{label_text}'")
            return
        
        # Find the container with date fields
        container = label.find_element(By.XPATH, "./ancestor::*[self::div or self::fieldset or self::form][1]")
        
        # Find date inputs - look for inputs that are specifically date fields
        # Filter by ID or name containing "date", "Date", "expiry", "Expiry", "issue", "Issue"
        date_inputs = container.find_elements(By.XPATH, ".//input[@type='text' or @type='date' or @type='']")
        
        # Filter to only include inputs that look like date fields
        filtered_date_inputs = []
        for input_elem in date_inputs:
            try:
                input_id = input_elem.get_attribute("id") or ""
                input_name = input_elem.get_attribute("name") or ""
                input_id_lower = input_id.lower()
                input_name_lower = input_name.lower()
                
                # Check if this looks like a date field
                is_date_field = (
                    "date" in input_id_lower or 
                    "date" in input_name_lower or
                    "expiry" in input_id_lower or
                    "expiry" in input_name_lower or
                    "issue" in input_id_lower or
                    "issue" in input_name_lower
                )
                
                if is_date_field:
                    filtered_date_inputs.append(input_elem)
            except:
                continue
        
        # If no filtered inputs found, use all inputs as fallback (but log warning)
        if not filtered_date_inputs:
            print(f"[WARN] No date-specific input fields found for '{label_text}', using all text inputs as fallback")
            filtered_date_inputs = date_inputs
        
        date_inputs = filtered_date_inputs
        
        if not date_inputs:
            print(f"[WARN] No date input fields found for '{label_text}'")
            return
        
        print(f"[DEBUG] Found {len(date_inputs)} date input fields")
        
        # Print debug information for each input field
        for idx, input_elem in enumerate(date_inputs):
            try:
                input_id = input_elem.get_attribute("id") or ""
                input_name = input_elem.get_attribute("name") or ""
                print(f"[DEBUG] Date input {idx + 1}: id='{input_id}', name='{input_name}'")
            except:
                pass
        
        # Extract keywords from label_text to identify the specific field
        label_text_lower = label_text.lower()
        is_issue_field = "issue" in label_text_lower
        is_expiry_field = "expiry" in label_text_lower or "expire" in label_text_lower
        
        print(f"[DEBUG] Label analysis: is_issue_field={is_issue_field}, is_expiry_field={is_expiry_field}")
        
        # Try to find the specific date field (From or To, or by label keywords)
        found = False
        for input_elem in date_inputs:
            try:
                if date_type:
                    # If date_type is provided, try to match by date_type (From/To) only
                    parent = input_elem.find_element(By.XPATH, "./..")
                    parent_text = parent.text
                    
                    # Also check preceding siblings for "From" or "To" labels
                    try:
                        preceding = input_elem.find_elements(By.XPATH, "./preceding-sibling::*")
                        for elem in preceding:
                            if date_type.lower() in elem.text.lower():
                                parent_text += " " + elem.text
                    except:
                        pass
                
                if date_type.lower() in parent_text.lower():
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                    time.sleep(0.5)
                    extended_wait.until(EC.element_to_be_clickable(input_elem))
                    input_elem.clear()
                    time.sleep(0.2)
                    input_elem.send_keys(date_value)
                    time.sleep(0.2)
                    print(f"[SUCCESS] Filled date {date_type} '{date_value}' in '{label_text}'")
                    found = True
                    break
                else:
                    # If date_type is empty, try to match by label keywords (Issue vs Expiry)
                    input_id = input_elem.get_attribute("id") or ""
                    input_name = input_elem.get_attribute("name") or ""
                    input_id_lower = input_id.lower()
                    input_name_lower = input_name.lower()
                    
                    # Check if this input matches the label keywords
                    input_is_issue = "issue" in input_id_lower or "issue" in input_name_lower
                    input_is_expiry = "expiry" in input_id_lower or "expire" in input_id_lower or "expiry" in input_name_lower or "expire" in input_name_lower
                    
                    print(f"[DEBUG] Input analysis: id='{input_id}', name='{input_name}', input_is_issue={input_is_issue}, input_is_expiry={input_is_expiry}")
                    
                    # Match Issue field
                    if is_issue_field and input_is_issue and not input_is_expiry:
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                        time.sleep(0.5)
                        extended_wait.until(EC.element_to_be_clickable(input_elem))
                        input_elem.clear()
                        time.sleep(0.2)
                        input_elem.send_keys(date_value)
                        time.sleep(0.2)
                        print(f"[SUCCESS] Filled date '{date_value}' in '{label_text}' (matched by Issue keyword)")
                        found = True
                        break
                    
                    # Match Expiry field
                    if is_expiry_field and input_is_expiry and not input_is_issue:
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                        time.sleep(0.5)
                        extended_wait.until(EC.element_to_be_clickable(input_elem))
                        input_elem.clear()
                        time.sleep(0.2)
                        input_elem.send_keys(date_value)
                        time.sleep(0.2)
                        print(f"[SUCCESS] Filled date '{date_value}' in '{label_text}' (matched by Expiry keyword)")
                        found = True
                        break
            except Exception as e:
                print(f"[DEBUG] Error processing input element: {e}")
                continue
        
        if not found:
            # Fallback: try to identify by position (first = From, second = To)
            if date_type and date_type.lower() == "from" and len(date_inputs) >= 1:
                input_elem = date_inputs[0]
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                time.sleep(0.5)
                extended_wait.until(EC.element_to_be_clickable(input_elem))
                input_elem.clear()
                time.sleep(0.2)
                input_elem.send_keys(date_value)
                print(f"[SUCCESS] Filled date {date_type} '{date_value}' in '{label_text}' (position-based)")
                found = True
            elif date_type and date_type.lower() == "to" and len(date_inputs) >= 2:
                input_elem = date_inputs[1]
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                time.sleep(0.5)
                extended_wait.until(EC.element_to_be_clickable(input_elem))
                input_elem.clear()
                time.sleep(0.2)
                input_elem.send_keys(date_value)
                print(f"[SUCCESS] Filled date {date_type} '{date_value}' in '{label_text}' (position-based)")
                found = True
            # Additional fallback: if only one date input found and label matches, use it
            elif len(date_inputs) == 1 and (is_issue_field or is_expiry_field):
                input_elem = date_inputs[0]
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                time.sleep(0.5)
                extended_wait.until(EC.element_to_be_clickable(input_elem))
                input_elem.clear()
                time.sleep(0.2)
                input_elem.send_keys(date_value)
                print(f"[SUCCESS] Filled date '{date_value}' in '{label_text}' (single field fallback)")
                found = True
            # Enhanced fallback: if we have 2 fields and one is issue, one is expiry, match by label
            elif len(date_inputs) == 2 and (is_issue_field or is_expiry_field):
                print(f"[DEBUG] Trying enhanced fallback: 2 fields found, label is {'issue' if is_issue_field else 'expiry'}")
                issue_input = None
                expiry_input = None
                
                for input_elem in date_inputs:
                    try:
                        input_id = input_elem.get_attribute("id") or ""
                        input_name = input_elem.get_attribute("name") or ""
                        input_id_lower = input_id.lower()
                        input_name_lower = input_name.lower()
                        
                        if "issue" in input_id_lower or "issue" in input_name_lower:
                            issue_input = input_elem
                        if "expiry" in input_id_lower or "expire" in input_id_lower or "expiry" in input_name_lower or "expire" in input_name_lower:
                            expiry_input = input_elem
                    except:
                        continue
                
                # Match based on label
                target_input = None
                if is_issue_field and issue_input:
                    target_input = issue_input
                    print(f"[DEBUG] Matched Issue field by ID/name")
                elif is_expiry_field and expiry_input:
                    target_input = expiry_input
                    print(f"[DEBUG] Matched Expiry field by ID/name")
                
                if target_input:
                    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_input)
                    time.sleep(0.5)
                    extended_wait.until(EC.element_to_be_clickable(target_input))
                    target_input.clear()
                    time.sleep(0.2)
                    target_input.send_keys(date_value)
                    time.sleep(0.2)
                    print(f"[SUCCESS] Filled date '{date_value}' in '{label_text}' (enhanced fallback match)")
                    found = True
                else:
                    # If we can't match by ID/name, try to match by position relative to label
                    # Date of Issue usually comes before Date of Expiry
                    if is_issue_field:
                        target_input = date_inputs[0]  # First field is usually Issue
                        print(f"[DEBUG] Using position-based match: Issue field should be first")
                    elif is_expiry_field:
                        target_input = date_inputs[1] if len(date_inputs) >= 2 else date_inputs[0]  # Second field is usually Expiry
                        print(f"[DEBUG] Using position-based match: Expiry field should be second")
                    
                    if target_input:
                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_input)
                        time.sleep(0.5)
                        extended_wait.until(EC.element_to_be_clickable(target_input))
                        target_input.clear()
                        time.sleep(0.2)
                        target_input.send_keys(date_value)
                        time.sleep(0.2)
                        print(f"[SUCCESS] Filled date '{date_value}' in '{label_text}' (position-based fallback)")
                found = True
        
        if not found:
            print(f"[WARN] Could not identify date field for '{label_text}' (date_type: '{date_type}')")
            # Print all available inputs for debugging
            for idx, input_elem in enumerate(date_inputs):
                try:
                    input_id = input_elem.get_attribute("id") or ""
                    input_name = input_elem.get_attribute("name") or ""
                    print(f"[DEBUG] Available input {idx + 1}: id='{input_id}', name='{input_name}'")
                except:
                    pass
        
    except Exception as e:
        print(f"[WARN] Could not fill date field '{label_text}': {str(e)[:200]}")


