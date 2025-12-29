from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import logging
import re

# ============================================================================
# Configuration: Operation delays to prevent server overload
# ============================================================================
# Delay between operations (in seconds)
OPERATION_DELAY = 1.5  # Delay between non-PostBack operations
POSTBACK_DELAY = 2.0  # Delay before triggering PostBack
POSTBACK_WAIT_DELAY = 3.0  # Delay after PostBack completes
POSTBACK_BETWEEN_DELAY = 2.5  # Delay between consecutive PostBack operations

def setup_logging():
    """Setup logging with timestamps"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # Force reconfiguration if already configured
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Explicitly set logger level
    return logger

# Initialize logger
logger = setup_logging()


def log_operation(operation_name, status="INFO", details=""):
    """
    Log operation with timestamp
    
    Args:
        operation_name: Name of the operation
        status: Status level (INFO, SUCCESS, WARN, ERROR)
        details: Additional details
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    status_prefix = {
        "INFO": "[INFO]",
        "SUCCESS": "[SUCCESS]",
        "WARN": "[WARN]",
        "ERROR": "[ERROR]"
    }.get(status, "[INFO]")
    
    message = f"{timestamp} {status_prefix} Operation: {operation_name}"
    if details:
        message += f" | {details}"
    
    print(message)
    logger.info(message)


def verify_page_state(browser, wait, expected_url_pattern=None, required_elements=None, operation_name=""):
    """
    Verify that the page is in the expected state before performing an operation
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        expected_url_pattern: Expected URL pattern (e.g., "VisaTypeDetails.aspx")
        required_elements: List of tuples (By, selector) for required elements
        operation_name: Name of the operation for logging
    
    Returns:
        bool: True if page state is valid, False otherwise
    """
    try:
        log_operation(f"verify_page_state ({operation_name})", "INFO", "Checking page state...")
        
        # Check URL
        current_url = browser.current_url
        if expected_url_pattern:
            if expected_url_pattern not in current_url:
                log_operation(f"verify_page_state ({operation_name})", "WARN", 
                            f"URL mismatch: expected '{expected_url_pattern}' in '{current_url}'")
                return False
        
        # Check document ready state
        ready_state = browser.execute_script("return document.readyState")
        if ready_state != "complete":
            log_operation(f"verify_page_state ({operation_name})", "WARN", 
                        f"Document not ready: {ready_state}")
            return False
        
        # Check for error page
        page_source_lower = browser.page_source.lower()
        error_keywords = ["error has occured", "error has occurred", "system administrator has been informed"]
        for keyword in error_keywords:
            if keyword in page_source_lower:
                log_operation(f"verify_page_state ({operation_name})", "ERROR", 
                            f"Error page detected: '{keyword}'")
                return False
        
        # Check required elements
        if required_elements:
            for by, selector in required_elements:
                try:
                    element = browser.find_element(by, selector)
                    if not element.is_displayed():
                        log_operation(f"verify_page_state ({operation_name})", "WARN", 
                                    f"Required element not visible: {by}={selector}")
                        return False
                except (NoSuchElementException, Exception) as e:
                    log_operation(f"verify_page_state ({operation_name})", "WARN", 
                                f"Required element not found: {by}={selector}, error: {str(e)[:100]}")
                    return False
        
        log_operation(f"verify_page_state ({operation_name})", "SUCCESS", "Page state verified")
        return True
        
    except Exception as e:
        log_operation(f"verify_page_state ({operation_name})", "ERROR", f"Exception: {str(e)[:200]}")
        return False


def safe_postback_operation(browser, wait, operation_name, operation_func, 
                           element_id=None, element_selector=None, 
                           delay_before=POSTBACK_DELAY, delay_after=POSTBACK_WAIT_DELAY):
    """
    Safely perform a PostBack operation with proper delays and state verification
    
    Args:
        browser: Selenium WebDriver instance
        wait: WebDriverWait instance
        operation_name: Name of the operation for logging
        operation_func: Function to execute the operation
        element_id: ID of the element that triggers PostBack (for verification)
        element_selector: Selector tuple (By, selector) for element verification
        delay_before: Delay before triggering PostBack
        delay_after: Delay after PostBack completes
    
    Returns:
        bool: True if operation succeeded, False otherwise
    """
    try:
        log_operation(operation_name, "INFO", "Starting PostBack operation...")
        
        # Verify page state before operation
        if not verify_page_state(browser, wait, 
                                expected_url_pattern="VisaTypeDetails.aspx",
                                operation_name=operation_name):
            log_operation(operation_name, "WARN", "Page state verification failed, but continuing...")
        
        # Delay before PostBack
        log_operation(operation_name, "INFO", f"Waiting {delay_before}s before PostBack...")
        time.sleep(delay_before)
        
        # Execute the operation
        log_operation(operation_name, "INFO", "Executing operation...")
        operation_func()
        
        # Wait for PostBack to start
        time.sleep(1)
        
        # Wait for document ready
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        
        # Wait for element to reappear (if element_id provided)
        if element_id:
            extended_wait = WebDriverWait(browser, 15)
            try:
                extended_wait.until(EC.presence_of_element_located((By.ID, element_id)))
                log_operation(operation_name, "INFO", f"Element {element_id} reappeared after PostBack")
            except TimeoutException:
                log_operation(operation_name, "WARN", f"Element {element_id} did not reappear within timeout")
        elif element_selector:
            extended_wait = WebDriverWait(browser, 15)
            try:
                extended_wait.until(EC.presence_of_element_located(element_selector))
                log_operation(operation_name, "INFO", f"Element {element_selector} reappeared after PostBack")
            except TimeoutException:
                log_operation(operation_name, "WARN", f"Element {element_selector} did not reappear within timeout")
        
        # Verify page state after PostBack
        current_url = browser.current_url
        if "OnlineHome.aspx" in current_url:
            log_operation(operation_name, "WARN", "Page redirected to homepage after PostBack")
            return False
        
        if "VisaTypeDetails.aspx" not in current_url:
            log_operation(operation_name, "WARN", f"Unexpected URL after PostBack: {current_url}")
            return False
        
        # Delay after PostBack
        log_operation(operation_name, "INFO", f"Waiting {delay_after}s after PostBack...")
        time.sleep(delay_after)
        
        # Check for error page (import here to avoid circular dependency)
        from insert_function.page_detection import check_and_handle_error_page
        check_and_handle_error_page(browser, wait)
        
        # Final verification
        if verify_page_state(browser, wait, 
                           expected_url_pattern="VisaTypeDetails.aspx",
                           operation_name=f"{operation_name} (final)"):
            log_operation(operation_name, "SUCCESS", "PostBack operation completed successfully")
            return True
        else:
            log_operation(operation_name, "WARN", "PostBack completed but page state verification failed")
            return False
            
    except Exception as e:
        log_operation(operation_name, "ERROR", f"Exception during PostBack: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

