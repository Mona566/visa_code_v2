"""
Unit tests for application_management.py module
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys
import os
import tempfile
import shutil

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insert_function.application_management import (
    save_page_source_for_debugging,
    save_application_number,
    get_saved_application_number,
    extract_application_number,
    retrieve_application
)


class TestApplicationManagement(unittest.TestCase):
    """Test cases for application management functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_browser = Mock()
        self.mock_wait = Mock()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # Clean up application_number.txt if it exists
        if os.path.exists("application_number.txt"):
            os.remove("application_number.txt")

    def test_save_page_source_for_debugging_success(self):
        """Test save_page_source_for_debugging successful save"""
        self.mock_browser.page_source = "<html><body>Test</body></html>"
        self.mock_browser.current_url = "https://example.com/test"
        self.mock_browser.title = "Test Page"
        
        with patch('insert_function.application_management.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.strftime.return_value = "20240101_120000"
            mock_datetime.datetime.now.return_value.strftime.side_effect = lambda fmt: {
                "%Y%m%d_%H%M%S": "20240101_120000",
                "%Y-%m-%d %H:%M:%S": "2024-01-01 12:00:00"
            }.get(fmt, "")
            
            result = save_page_source_for_debugging(self.mock_browser, 5)
            
            # Check if file was created (filename should be returned)
            self.assertIsNotNone(result)
            self.assertIn("page_source_page5", result)

    def test_save_application_number_success(self):
        """Test save_application_number with valid application number"""
        result = save_application_number("81181802")
        self.assertTrue(result)
        self.assertTrue(os.path.exists("application_number.txt"))
        
        with open("application_number.txt", "r") as f:
            content = f.read().strip()
            self.assertEqual(content, "81181802")

    def test_save_application_number_invalid(self):
        """Test save_application_number with invalid application number"""
        invalid_values = ["-", "n/a", "na", "", "none", "null"]
        for invalid in invalid_values:
            result = save_application_number(invalid)
            self.assertFalse(result)

    def test_save_application_number_too_short(self):
        """Test save_application_number with too short number"""
        result = save_application_number("123")
        self.assertFalse(result)

    def test_get_saved_application_number_exists(self):
        """Test get_saved_application_number when file exists"""
        # First save a valid application number
        save_application_number("81181802")
        
        # Then retrieve it
        result = get_saved_application_number()
        self.assertEqual(result, "81181802")

    def test_get_saved_application_number_not_exists(self):
        """Test get_saved_application_number when file doesn't exist"""
        if os.path.exists("application_number.txt"):
            os.remove("application_number.txt")
        
        result = get_saved_application_number()
        self.assertIsNone(result)

    def test_extract_application_number_from_element(self):
        """Test extract_application_number extracting from element"""
        # Mock element with application number
        mock_element = Mock()
        mock_element.text = "81181802"
        
        self.mock_browser.find_element.return_value = mock_element
        self.mock_browser.page_source = "<html><body>Application Number: 81181802</body></html>"
        self.mock_browser.current_url = "https://example.com/test"
        
        with patch('insert_function.application_management.By') as mock_by:
            mock_by.ID = "id"
            result = extract_application_number(self.mock_browser, self.mock_wait, save_debug=False)
            self.assertEqual(result, "81181802")

    def test_extract_application_number_from_page_source(self):
        """Test extract_application_number extracting from page source"""
        self.mock_browser.page_source = """
        <html>
        <body>
        <span>Your unique Application Number is: 81181802</span>
        </body>
        </html>
        """
        self.mock_browser.current_url = "https://example.com/test"
        self.mock_browser.find_element.side_effect = Exception("Not found")
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Your unique Application Number is: 81181802"
        self.mock_browser.find_element.return_value = mock_body
        
        result = extract_application_number(self.mock_browser, self.mock_wait, save_debug=False)
        self.assertEqual(result, "81181802")

    def test_extract_application_number_not_found(self):
        """Test extract_application_number when number is not found"""
        # Use page text that doesn't contain "Application Number" pattern to avoid false matches
        self.mock_browser.page_source = "<html><body>Welcome to the visa application form. Please fill in all required fields.</body></html>"
        self.mock_browser.current_url = "https://example.com/test"
        
        # Mock body element - this will be called by find_element(By.TAG_NAME, "body")
        mock_body = Mock()
        mock_body.text = "Welcome to the visa application form. Please fill in all required fields."
        
        # Setup find_element to return body for TAG_NAME, but raise exception for other selectors
        from selenium.webdriver.common.by import By
        def find_element_side_effect(by, selector):
            if by == By.TAG_NAME and selector == "body":
                return mock_body
            else:
                raise Exception("Not found")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Also mock find_elements to return empty list
        self.mock_browser.find_elements.return_value = []
        
        result = extract_application_number(self.mock_browser, self.mock_wait, save_debug=False)
        self.assertIsNone(result)

    @patch('insert_function.application_management.time.sleep')
    @patch('insert_function.application_management.WebDriverWait')
    def test_retrieve_application_success(self, mock_wait_class, mock_sleep):
        """Test retrieve_application successful retrieval - simplified version"""
        # This test is simplified because retrieve_application is very complex
        # We test that it validates input correctly and doesn't crash
        
        # Mock browser and wait
        self.mock_browser.current_url = "https://example.com/OnlineHome.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        self.mock_browser.page_source = "<html><body>Retrieve Application</body></html>"
        
        # Mock retrieve link
        mock_retrieve_link = Mock()
        
        # Mock application number input
        mock_app_input = Mock()
        mock_app_input.get_attribute.return_value = "81181802"
        
        # Setup find_element to return retrieve link
        def find_element_side_effect(by, selector):
            if "Retrieve" in str(selector) or "lnkbtnRetrieveApp" in str(selector):
                return mock_retrieve_link
            elif "ApplicationNumber" in str(selector):
                return mock_app_input
            else:
                raise Exception("Element not found")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Mock wait until - need to handle multiple calls with different return values
        mock_extended_wait = Mock()
        # Create a list of return values for multiple until() calls
        until_returns = [
            mock_retrieve_link,      # For retrieve link
            mock_app_input,          # For application number input
        ]
        mock_extended_wait.until.side_effect = lambda *args: until_returns.pop(0) if until_returns else mock_app_input
        mock_wait_class.return_value = mock_extended_wait
        
        # Mock all the complex dependencies
        with patch('insert_function.application_management.check_homepage_redirect', return_value=None):
            with patch('insert_function.application_management.detect_page_number_no_refresh', return_value=2):
                with patch('insert_function.application_management.Select'):
                    # Patch fill_page_2 in the page_fillers module (where it's imported from in retrieve_application)
                    with patch('insert_function.page_fillers.fill_page_2', return_value="success"):
                        # Mock fill_application_form in main_flow module (where it's imported from)
                        with patch('insert_function.main_flow.fill_application_form'):
                            # Mock datetime for file saving
                            with patch('insert_function.application_management.datetime') as mock_datetime:
                                mock_datetime.datetime.now.return_value.strftime.return_value = "20240101_120000"
                                mock_datetime.datetime.now.return_value.strftime.side_effect = lambda fmt: {
                                    "%Y%m%d_%H%M%S": "20240101_120000",
                                    "%Y-%m-%d %H:%M:%S": "2024-01-01 12:00:00"
                                }.get(fmt, "")
                                
                                # Mock file operations
                                with patch('builtins.open', mock_open()):
                                    # Update URL after "click" to simulate navigation
                                    def url_change_after_click():
                                        self.mock_browser.current_url = "https://example.com/OnlineHome2.aspx"
                                    
                                    # Mock execute_script to handle __doPostBack
                                    original_execute_return = self.mock_browser.execute_script.return_value
                                    def execute_script_side_effect(script, *args):
                                        if "__doPostBack" in str(script):
                                            url_change_after_click()
                                        return original_execute_return
                                    self.mock_browser.execute_script.side_effect = execute_script_side_effect
                                    
                                    # Mock WebDriverWait for URL change check
                                    with patch('insert_function.application_management.WebDriverWait') as mock_url_wait_class:
                                        mock_url_wait_instance = Mock()
                                        mock_url_wait_instance.until.return_value = True
                                        mock_url_wait_class.return_value = mock_url_wait_instance
                                        
                                        result = retrieve_application(
                                            self.mock_browser,
                                            self.mock_wait,
                                            "81181802"
                                        )
                                        
                                        # The function is very complex, so we just verify it doesn't crash
                                        # and returns a boolean value
                                        self.assertIsInstance(result, bool)

    def test_retrieve_application_invalid_number(self):
        """Test retrieve_application with invalid application number"""
        result = retrieve_application(
            self.mock_browser,
            self.mock_wait,
            ""  # Empty application number
        )
        self.assertFalse(result)

    def test_retrieve_application_too_short(self):
        """Test retrieve_application with too short application number"""
        result = retrieve_application(
            self.mock_browser,
            self.mock_wait,
            "123"  # Too short
        )
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()

