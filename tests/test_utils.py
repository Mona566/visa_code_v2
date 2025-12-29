"""
Unit tests for utils.py module
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import logging

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insert_function.utils import (
    setup_logging,
    log_operation,
    verify_page_state,
    safe_postback_operation,
    OPERATION_DELAY,
    POSTBACK_DELAY,
    POSTBACK_WAIT_DELAY,
    POSTBACK_BETWEEN_DELAY
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions"""

    def test_setup_logging(self):
        """Test setup_logging function"""
        logger = setup_logging()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.INFO)

    def test_log_operation_info(self):
        """Test log_operation with INFO status"""
        with patch('insert_function.utils.logger') as mock_logger:
            log_operation("test_operation", "INFO", "Test details")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("test_operation", call_args)
            self.assertIn("[INFO]", call_args)
            self.assertIn("Test details", call_args)

    def test_log_operation_success(self):
        """Test log_operation with SUCCESS status"""
        with patch('insert_function.utils.logger') as mock_logger:
            log_operation("test_operation", "SUCCESS", "Operation completed")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("[SUCCESS]", call_args)

    def test_log_operation_warn(self):
        """Test log_operation with WARN status"""
        with patch('insert_function.utils.logger') as mock_logger:
            log_operation("test_operation", "WARN", "Warning message")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("[WARN]", call_args)

    def test_log_operation_error(self):
        """Test log_operation with ERROR status"""
        with patch('insert_function.utils.logger') as mock_logger:
            log_operation("test_operation", "ERROR", "Error message")
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            self.assertIn("[ERROR]", call_args)

    def test_verify_page_state_success(self):
        """Test verify_page_state with valid page state"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "complete"
        mock_browser.page_source = "<html><body>No errors</body></html>"
        
        mock_wait = Mock()
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            operation_name="test"
        )
        self.assertTrue(result)

    def test_verify_page_state_url_mismatch(self):
        """Test verify_page_state with URL mismatch"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/OtherPage.aspx"
        mock_browser.execute_script.return_value = "complete"
        mock_browser.page_source = "<html><body>No errors</body></html>"
        
        mock_wait = Mock()
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            operation_name="test"
        )
        self.assertFalse(result)

    def test_verify_page_state_not_ready(self):
        """Test verify_page_state when document is not ready"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "loading"
        mock_browser.page_source = "<html><body>No errors</body></html>"
        
        mock_wait = Mock()
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            operation_name="test"
        )
        self.assertFalse(result)

    def test_verify_page_state_error_page(self):
        """Test verify_page_state with error page"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "complete"
        mock_browser.page_source = "<html><body>An error has occurred</body></html>"
        
        mock_wait = Mock()
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            operation_name="test"
        )
        self.assertFalse(result)

    def test_verify_page_state_with_required_elements(self):
        """Test verify_page_state with required elements"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "complete"
        mock_browser.page_source = "<html><body>No errors</body></html>"
        
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        mock_browser.find_element.return_value = mock_element
        
        mock_wait = Mock()
        
        from selenium.webdriver.common.by import By
        required_elements = [(By.ID, "test_element")]
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            required_elements=required_elements,
            operation_name="test"
        )
        self.assertTrue(result)

    def test_verify_page_state_missing_element(self):
        """Test verify_page_state when required element is missing"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "complete"
        mock_browser.page_source = "<html><body>No errors</body></html>"
        mock_browser.find_element.side_effect = Exception("Element not found")
        
        mock_wait = Mock()
        
        from selenium.webdriver.common.by import By
        required_elements = [(By.ID, "missing_element")]
        
        result = verify_page_state(
            mock_browser, 
            mock_wait, 
            expected_url_pattern="VisaTypeDetails.aspx",
            required_elements=required_elements,
            operation_name="test"
        )
        self.assertFalse(result)

    @patch('insert_function.utils.time.sleep')
    @patch('insert_function.utils.verify_page_state')
    def test_safe_postback_operation_success(self, mock_verify, mock_sleep):
        """Test safe_postback_operation successful execution"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        mock_browser.execute_script.return_value = "complete"
        
        mock_wait = Mock()
        mock_wait.until.return_value = True
        
        mock_element = Mock()
        mock_browser.find_element.return_value = mock_element
        
        operation_func = Mock()
        mock_verify.return_value = True
        
        result = safe_postback_operation(
            mock_browser,
            mock_wait,
            "test_operation",
            operation_func,
            element_id="test_element"
        )
        
        self.assertTrue(result)
        operation_func.assert_called_once()
        mock_sleep.assert_called()

    @patch('insert_function.utils.time.sleep')
    @patch('insert_function.utils.verify_page_state')
    def test_safe_postback_operation_homepage_redirect(self, mock_verify, mock_sleep):
        """Test safe_postback_operation when redirected to homepage"""
        mock_browser = Mock()
        mock_browser.current_url = "https://example.com/OnlineHome.aspx"
        mock_browser.execute_script.return_value = "complete"
        
        mock_wait = Mock()
        mock_wait.until.return_value = True
        
        operation_func = Mock()
        mock_verify.return_value = True
        
        result = safe_postback_operation(
            mock_browser,
            mock_wait,
            "test_operation",
            operation_func
        )
        
        self.assertFalse(result)

    def test_constants(self):
        """Test that constants are defined correctly"""
        self.assertEqual(OPERATION_DELAY, 1.5)
        self.assertEqual(POSTBACK_DELAY, 2.0)
        self.assertEqual(POSTBACK_WAIT_DELAY, 3.0)
        self.assertEqual(POSTBACK_BETWEEN_DELAY, 2.5)


if __name__ == '__main__':
    import logging
    unittest.main()

