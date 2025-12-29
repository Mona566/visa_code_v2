"""
Unit tests for form_helpers.py module
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insert_function.form_helpers import (
    fill_dropdown_by_label,
    select_radio_by_label,
    fill_text_by_label,
    fill_date_by_label
)


class TestFormHelpers(unittest.TestCase):
    """Test cases for form helper functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_browser = Mock()
        self.mock_wait = Mock()
        self.mock_wait.until.return_value = True

    def test_fill_dropdown_by_label_success(self):
        """Test fill_dropdown_by_label with successful selection"""
        # Mock label element
        mock_label = Mock()
        mock_label.get_attribute.return_value = "test_select_id"
        mock_label.find_element.side_effect = Exception("Not found")
        
        # Mock select element
        mock_select_element = Mock()
        mock_select_element.get_attribute.return_value = "test_select_id"
        mock_select_element.is_displayed.return_value = True
        
        # Mock Select object
        mock_select = Mock()
        mock_option = Mock()
        mock_option.text = "Test Value"
        mock_select.options = [mock_option]
        mock_select.first_selected_option.text = "Test Value"
        
        self.mock_browser.find_element.return_value = mock_select_element
        self.mock_browser.execute_script.return_value = False  # No PostBack
        
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            mock_extended_wait.until.return_value = mock_label
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.Select', return_value=mock_select):
                with patch('insert_function.form_helpers.time.sleep'):
                    fill_dropdown_by_label(
                        self.mock_browser,
                        self.mock_wait,
                        "Test Label",
                        "Test Value"
                    )
                    
                    # Verify select_by_visible_text was called
                    mock_select.select_by_visible_text.assert_called()

    def test_fill_dropdown_by_label_label_not_found(self):
        """Test fill_dropdown_by_label when label is not found"""
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            mock_extended_wait.until.side_effect = Exception("Timeout")
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.time.sleep'):
                # Should not raise exception, just return
                fill_dropdown_by_label(
                    self.mock_browser,
                    self.mock_wait,
                    "Non-existent Label",
                    "Test Value"
                )

    def test_select_radio_by_label_success(self):
        """Test select_radio_by_label with successful selection"""
        # Mock container element (found by find_elements)
        mock_container = Mock()
        mock_container.text = "Test Label"
        
        # Mock parent element
        mock_parent = Mock()
        
        # Mock radio element
        mock_radio = Mock()
        mock_radio.get_attribute.return_value = "test_radio_id"
        mock_radio.is_displayed.return_value = True
        mock_radio.is_selected.return_value = False
        
        # Mock radio label (found by browser.find_element with label[@for])
        # Use MagicMock so we can set text as a property that supports .strip()
        mock_radio_label = MagicMock()
        # Set text as a string property - when code calls text.strip(), it will work
        type(mock_radio_label).text = "Test Value"
        
        # Setup container to find parent and radios
        mock_container.find_element.return_value = mock_parent
        mock_parent.find_elements.return_value = [mock_radio]
        
        # Setup browser to find radio label and body
        from selenium.webdriver.common.by import By
        call_count = [0]
        def find_element_side_effect(by, selector):
            call_count[0] += 1
            if by == By.XPATH and "label[@for='test_radio_id']" in str(selector):
                return mock_radio_label
            elif by == By.TAG_NAME and selector == "body":
                mock_body = Mock()
                mock_body.text = "Test Label Test Value"
                return mock_body
            elif by == By.ID and selector == "test_radio_id":
                # Return radio when re-finding by ID
                return mock_radio
            else:
                raise Exception(f"Element not found: {by}={selector}")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Mock find_elements to return container list
        def find_elements_side_effect(by, selector):
            if "Test Label" in str(selector):
                return [mock_container]
            return []
        
        self.mock_browser.find_elements.side_effect = find_elements_side_effect
        self.mock_browser.execute_script.return_value = False  # No PostBack
        
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            # For EC.element_to_be_clickable - return radio
            mock_extended_wait.until.return_value = mock_radio
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.time.sleep'):
                select_radio_by_label(
                    self.mock_browser,
                    self.mock_wait,
                    "Test Label",
                    "Test Value"
                )
                
                # Verify click was called (or JavaScript click/checked property set)
                # The function may use different methods, so we check if any interaction happened
                # It should have tried to click or set the checked property
                self.assertTrue(
                    mock_radio.click.called or 
                    len([call for call in (self.mock_browser.execute_script.call_args_list or []) if call and ("click" in str(call) or "checked" in str(call))]) > 0
                )

    def test_fill_text_by_label_success(self):
        """Test fill_text_by_label with successful input"""
        # Mock label element (found by find_elements)
        mock_label = Mock()
        mock_label.get_attribute.return_value = "test_input_id"
        mock_label.text = "Test Label"
        
        # Mock input element (found near label)
        mock_input = Mock()
        mock_input.get_attribute.return_value = "Test Value"
        mock_input.is_displayed.return_value = True
        
        # Setup label to find nearby inputs
        mock_label.find_elements.return_value = [mock_input]
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Test Label"
        
        # Setup find_element for body and radio label lookup
        from selenium.webdriver.common.by import By
        def find_element_side_effect(by, selector):
            if by == By.TAG_NAME and selector == "body":
                return mock_body
            elif by == By.ID and selector == "test_input_id":
                return mock_input
            else:
                raise Exception("Element not found")
        
        self.mock_browser.find_element.side_effect = find_element_side_effect
        
        # Mock find_elements to return label list
        def find_elements_side_effect(by, selector):
            if "Test Label" in str(selector):
                return [mock_label]
            return []
        
        self.mock_browser.find_elements.side_effect = find_elements_side_effect
        self.mock_browser.execute_script.return_value = False  # No PostBack
        
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            # For EC.element_to_be_clickable
            mock_extended_wait.until.return_value = mock_input
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.time.sleep'):
                fill_text_by_label(
                    self.mock_browser,
                    self.mock_wait,
                    "Test Label",
                    "Test Value"
                )
                
                # Verify clear and send_keys were called
                mock_input.clear.assert_called()
                mock_input.send_keys.assert_called_with("Test Value")

    def test_fill_date_by_label_success(self):
        """Test fill_date_by_label with successful date input"""
        # Mock label element (found by extended_wait.until)
        mock_label = Mock()
        mock_label.text = "Date of Birth"
        
        # Mock container element
        mock_container = Mock()
        
        # Mock date input element
        mock_date_input = Mock()
        mock_date_input.get_attribute.side_effect = lambda attr: {
            "id": "test_date_id",
            "name": "test_date_name",
            "type": "text"
        }.get(attr, "")
        mock_date_input.is_displayed.return_value = True
        
        # Mock parent element (for date_type matching)
        mock_parent = Mock()
        mock_parent.text = "Day"  # Contains date_type
        
        # Setup label to find container
        mock_label.find_element.return_value = mock_container
        
        # Setup container to find date inputs
        mock_container.find_elements.return_value = [mock_date_input]
        
        # Setup date input to find parent
        mock_date_input.find_element.return_value = mock_parent
        mock_date_input.find_elements.return_value = []  # No preceding siblings
        
        self.mock_browser.execute_script.return_value = False  # No PostBack
        
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            # First until() returns label, second returns date_input (for element_to_be_clickable)
            mock_extended_wait.until.side_effect = [mock_label, mock_date_input]
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.time.sleep'):
                fill_date_by_label(
                    self.mock_browser,
                    self.mock_wait,
                    "Date of Birth",
                    "Day",
                    "01/01/2024"
                )
                
                # Verify clear and send_keys were called
                mock_date_input.clear.assert_called()
                mock_date_input.send_keys.assert_called_with("01/01/2024")

    def test_fill_dropdown_by_label_with_postback(self):
        """Test fill_dropdown_by_label with PostBack behavior"""
        # Mock label element
        mock_label = Mock()
        mock_label.get_attribute.return_value = "test_select_id"
        
        # Mock select element
        mock_select_element = Mock()
        mock_select_element.get_attribute.return_value = "test_select_id"
        mock_select_element.is_displayed.return_value = True
        
        # Mock Select object
        mock_select = Mock()
        mock_option = Mock()
        mock_option.text = "Test Value"
        mock_select.options = [mock_option]
        mock_select.first_selected_option.text = "Test Value"
        
        self.mock_browser.find_element.return_value = mock_select_element
        self.mock_browser.execute_script.return_value = True  # Has PostBack
        self.mock_browser.current_url = "https://example.com/VisaTypeDetails.aspx"
        
        with patch('insert_function.form_helpers.WebDriverWait') as mock_wait_class:
            mock_extended_wait = Mock()
            mock_extended_wait.until.return_value = mock_label
            mock_wait_class.return_value = mock_extended_wait
            
            with patch('insert_function.form_helpers.Select', return_value=mock_select):
                with patch('insert_function.form_helpers.time.sleep'):
                    with patch('insert_function.form_helpers.log_operation'):
                        fill_dropdown_by_label(
                            self.mock_browser,
                            self.mock_wait,
                            "Test Label",
                            "Test Value"
                        )
                        
                        # Verify select_by_visible_text was called
                        mock_select.select_by_visible_text.assert_called()


if __name__ == '__main__':
    unittest.main()

