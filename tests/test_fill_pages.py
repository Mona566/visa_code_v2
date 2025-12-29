"""
Unit tests for fill_page_*.py modules
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insert_function.fill_page_1 import fill_page_1
from insert_function.fill_page_2 import fill_page_2
from insert_function.fill_page_3 import fill_page_3
from insert_function.fill_page_4 import fill_page_4
from insert_function.fill_page_5 import fill_page_5
from insert_function.fill_page_6 import fill_page_6
from insert_function.fill_page_7 import fill_page_7
from insert_function.fill_page_8 import fill_page_8
from insert_function.fill_page_9 import fill_page_9
from insert_function.fill_page_10 import fill_page_10


class TestFillPages(unittest.TestCase):
    """Test cases for page filling functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_browser = Mock()
        self.mock_wait = Mock()
        self.mock_wait.until.return_value = True

    def test_fill_page_1_homepage_redirect(self):
        """Test fill_page_1 when redirected to homepage"""
        self.mock_browser.current_url = "https://example.com/OnlineHome.aspx"
        
        with patch('insert_function.fill_page_1.check_homepage_redirect', return_value="homepage"):
            result = fill_page_1(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_1.time.sleep')
    @patch('insert_function.fill_page_1.check_homepage_redirect')
    def test_fill_page_2_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_2 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        self.mock_browser.page_source = "<html><body>Page 2</body></html>"
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Page 2"
        self.mock_browser.find_element.return_value = mock_body
        
        with patch('insert_function.fill_page_2.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_2.click_next_button', return_value=True):
                result = fill_page_2(self.mock_browser, self.mock_wait)
                # Should return success or a page number
                self.assertIsNotNone(result)

    @patch('insert_function.fill_page_3.time.sleep')
    @patch('insert_function.fill_page_3.check_homepage_redirect')
    def test_fill_page_3_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_3 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_3.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_3.click_next_button', return_value=True):
                result = fill_page_3(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    @patch('insert_function.fill_page_4.time.sleep')
    @patch('insert_function.fill_page_4.check_homepage_redirect')
    def test_fill_page_4_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_4 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_4.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_4.click_next_button', return_value=True):
                result = fill_page_4(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    @patch('insert_function.fill_page_5.time.sleep')
    @patch('insert_function.fill_page_5.check_homepage_redirect')
    def test_fill_page_5_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_5 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_5.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_5.click_next_button', return_value=True):
                result = fill_page_5(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    def test_fill_page_2_homepage_redirect(self):
        """Test fill_page_2 when redirected to homepage"""
        with patch('insert_function.fill_page_2.check_homepage_redirect', return_value="homepage"):
            result = fill_page_2(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_6.time.sleep')
    @patch('insert_function.fill_page_6.check_homepage_redirect')
    def test_fill_page_6_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_6 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_6.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_6.click_next_button', return_value=True):
                result = fill_page_6(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    def test_fill_page_6_homepage_redirect(self):
        """Test fill_page_6 when redirected to homepage"""
        with patch('insert_function.fill_page_6.check_homepage_redirect', return_value="homepage"):
            result = fill_page_6(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_7.time.sleep')
    @patch('insert_function.fill_page_7.check_homepage_redirect')
    def test_fill_page_7_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_7 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_7.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_7.click_next_button', return_value=True):
                result = fill_page_7(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    def test_fill_page_7_homepage_redirect(self):
        """Test fill_page_7 when redirected to homepage"""
        with patch('insert_function.fill_page_7.check_homepage_redirect', return_value="homepage"):
            result = fill_page_7(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_8.time.sleep')
    @patch('insert_function.fill_page_8.check_homepage_redirect')
    def test_fill_page_8_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_8 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_8.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_8.click_next_button', return_value=True):
                result = fill_page_8(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    def test_fill_page_8_homepage_redirect(self):
        """Test fill_page_8 when redirected to homepage"""
        with patch('insert_function.fill_page_8.check_homepage_redirect', return_value="homepage"):
            result = fill_page_8(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_9.time.sleep')
    @patch('insert_function.fill_page_9.check_homepage_redirect')
    def test_fill_page_9_success(self, mock_check_redirect, mock_sleep):
        """Test fill_page_9 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        
        with patch('insert_function.fill_page_9.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_9.click_next_button', return_value=True):
                result = fill_page_9(self.mock_browser, self.mock_wait)
                self.assertIsNotNone(result)

    def test_fill_page_9_homepage_redirect(self):
        """Test fill_page_9 when redirected to homepage"""
        with patch('insert_function.fill_page_9.check_homepage_redirect', return_value="homepage"):
            result = fill_page_9(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_10.time.sleep')
    @patch('insert_function.fill_page_10.check_homepage_redirect')
    @patch('builtins.input', return_value='')  # Mock input() to avoid EOF error
    @patch('builtins.open', create=True)  # Mock file operations
    def test_fill_page_10_success(self, mock_open, mock_input, mock_check_redirect, mock_sleep):
        """Test fill_page_10 successful filling"""
        mock_check_redirect.return_value = None
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        self.mock_browser.page_source = """
        <html>
        <body>
        <span>Thank you for your submission</span>
        </body>
        </html>
        """
        self.mock_browser.title = "Page 10"
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Thank you for your submission"
        
        # Mock radio button element
        mock_radio = Mock()
        mock_radio.is_selected.return_value = True
        mock_radio.is_displayed.return_value = True
        
        # Mock find_element to return different elements
        from selenium.webdriver.common.by import By
        def find_element_side_effect(by, selector):
            if by == By.TAG_NAME and selector == "body":
                return mock_body
            elif "rdblstAgency" in str(selector):
                return mock_radio
            else:
                raise Exception("Element not found")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Mock find_elements to return empty list (for MainHeadersText check)
        self.mock_browser.find_elements.return_value = []
        
        with patch('insert_function.fill_page_10.extract_application_number', return_value=None):
            with patch('insert_function.fill_page_10.save_application_number'):
                with patch('insert_function.fill_page_10.click_next_button', return_value=True):
                    with patch('insert_function.fill_page_10.verify_page_state', return_value=True):
                        with patch('insert_function.fill_page_10.WebDriverWait') as mock_wait_class:
                            with patch('insert_function.fill_page_10.datetime') as mock_datetime:
                                mock_datetime.datetime.now.return_value.strftime.return_value = "20240101_120000"
                                mock_datetime.datetime.now.return_value.strftime.side_effect = lambda fmt: {
                                    "%Y%m%d_%H%M%S": "20240101_120000",
                                    "%Y-%m-%d %H:%M:%S": "2024-01-01 12:00:00"
                                }.get(fmt, "")
                                
                                mock_extended_wait = Mock()
                                mock_extended_wait.until.return_value = mock_radio
                                mock_wait_class.return_value = mock_extended_wait
                                
                                result = fill_page_10(self.mock_browser, self.mock_wait)
                                # fill_page_10 should return success or a page number
                                self.assertIsNotNone(result)

    def test_fill_page_10_homepage_redirect(self):
        """Test fill_page_10 when redirected to homepage"""
        with patch('insert_function.fill_page_10.check_homepage_redirect', return_value="homepage"):
            result = fill_page_10(self.mock_browser, self.mock_wait)
            self.assertEqual(result, "homepage_redirect")

    @patch('insert_function.fill_page_10.time.sleep')
    @patch('builtins.input', return_value='')  # Mock input() to avoid EOF error
    @patch('builtins.open', create=True)  # Mock file operations
    def test_fill_page_10_submission_complete(self, mock_open, mock_input, mock_sleep):
        """Test fill_page_10 when submission is complete"""
        self.mock_browser.current_url = "https://example.com/CompleteFormSummary.aspx"
        self.mock_browser.execute_script.return_value = "complete"
        self.mock_browser.page_source = """
        <html>
        <body>
        <span>Your online application has been submitted</span>
        </body>
        </html>
        """
        self.mock_browser.title = "Submission Complete"
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Your online application has been submitted"
        
        # Mock find_element to return body
        from selenium.webdriver.common.by import By
        def find_element_side_effect(by, selector):
            if by == By.TAG_NAME and selector == "body":
                return mock_body
            else:
                raise Exception("Element not found")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Mock find_elements to return empty list (for MainHeadersText check)
        self.mock_browser.find_elements.return_value = []
        
        with patch('insert_function.fill_page_10.check_homepage_redirect', return_value=None):
            with patch('insert_function.fill_page_10.extract_application_number', return_value="81181802"):
                with patch('insert_function.fill_page_10.save_application_number'):
                    with patch('insert_function.fill_page_10.datetime') as mock_datetime:
                        mock_datetime.datetime.now.return_value.strftime.return_value = "20240101_120000"
                        mock_datetime.datetime.now.return_value.strftime.side_effect = lambda fmt: {
                            "%Y%m%d_%H%M%S": "20240101_120000",
                            "%Y-%m-%d %H:%M:%S": "2024-01-01 12:00:00"
                        }.get(fmt, "")
                        
                        result = fill_page_10(self.mock_browser, self.mock_wait)
                        # Should return "submission_complete" when on CompleteFormSummary.aspx
                        self.assertEqual(result, "submission_complete")


if __name__ == '__main__':
    unittest.main()

