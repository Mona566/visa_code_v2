"""
Unit tests for llm_analysis.py module
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import json
import re

# Mock dependencies before importing llm_analysis
mock_dotenv = MagicMock()
sys.modules['dotenv'] = mock_dotenv
sys.modules['langchain_openai'] = MagicMock()
mock_chat_openai_class = MagicMock()
sys.modules['langchain_openai.ChatOpenAI'] = mock_chat_openai_class

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock os.environ before importing (llm_analysis uses os.environ.get("MODEL"))
with patch.dict(os.environ, {'MODEL': 'gpt-4'}):
    from llm_analysis import extract_visa_fields, irish_visa_template_prompt


class TestLlmAnalysis(unittest.TestCase):
    """Test cases for LLM analysis functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_markdown = """
        Passport Number: AB123456
        Name: John Doe
        Date of Birth: 1990-01-01
        Nationality: Chinese
        """
        
        self.sample_fields = {
            "Application Information": {
                "visa_type": "Long Stay (D)",
                "journey_type": "Multiple",
                "reason_for_travel": "Study"
            },
            "Personal Information": {
                "surname": "Doe",
                "forename": "John",
                "date_of_birth": "1990-01-01",
                "nationality": "Chinese"
            }
        }

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_success(self, mock_llm):
        """Test extract_visa_fields successful extraction"""
        # Setup mock LLM response
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_fields, ensure_ascii=False)
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Verify LLM was called with correct prompt
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIn(self.sample_markdown, call_args)
        self.assertIn("爱尔兰签证材料字段识别专家", call_args)
        
        # Verify result
        self.assertEqual(result, self.sample_fields)
        self.assertIn("Personal Information", result)
        self.assertEqual(result["Personal Information"]["surname"], "Doe")

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_json_in_code_block(self, mock_llm):
        """Test extract_visa_fields when JSON is in code block"""
        # Setup mock LLM response with JSON in markdown code block
        json_with_markdown = f"```json\n{json.dumps(self.sample_fields)}\n```"
        mock_response = Mock()
        mock_response.content = json_with_markdown
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Should extract JSON from code block
        self.assertEqual(result, self.sample_fields)

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_json_with_text(self, mock_llm):
        """Test extract_visa_fields when JSON is mixed with text"""
        # Setup mock LLM response with text before JSON
        response_text = f"Here is the extracted information:\n{json.dumps(self.sample_fields)}"
        mock_response = Mock()
        mock_response.content = response_text
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Should extract JSON from text
        self.assertEqual(result, self.sample_fields)

    @patch('llm_analysis.llm')
    @patch('builtins.print')  # Suppress warning output during test
    def test_extract_visa_fields_invalid_json_fixes(self, mock_print, mock_llm):
        """Test extract_visa_fields when JSON is invalid and gets fixed"""
        # First response has invalid JSON
        invalid_json = '{"key": "value",}'  # trailing comma
        mock_response1 = Mock()
        mock_response1.content = invalid_json
        
        # Second response (fix attempt) has valid JSON
        mock_response2 = Mock()
        mock_response2.content = json.dumps(self.sample_fields)
        
        mock_llm.invoke.side_effect = [mock_response1, mock_response2]
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Should have called LLM twice (once for extraction, once for fixing)
        self.assertEqual(mock_llm.invoke.call_count, 2)
        self.assertEqual(result, self.sample_fields)

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_no_json_in_response(self, mock_llm):
        """Test extract_visa_fields when response has no JSON"""
        # Setup mock LLM response with no JSON
        mock_response = Mock()
        mock_response.content = "I cannot extract the information from this text."
        mock_llm.invoke.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            extract_visa_fields(self.sample_markdown)
        self.assertIn("未找到JSON格式", str(context.exception))

    @patch('llm_analysis.llm')
    @patch('builtins.print')  # Suppress warning output during test
    def test_extract_visa_fields_fix_fails(self, mock_print, mock_llm):
        """Test extract_visa_fields when JSON fix also fails"""
        # Both responses have invalid JSON
        invalid_json1 = '{"key": "value",}'
        invalid_json2 = '{"key": "value", "missing": }'
        
        mock_response1 = Mock()
        mock_response1.content = invalid_json1
        mock_response2 = Mock()
        mock_response2.content = invalid_json2
        
        mock_llm.invoke.side_effect = [mock_response1, mock_response2]
        
        with self.assertRaises(ValueError) as context:
            extract_visa_fields(self.sample_markdown)
        self.assertIn("无法解析LLM返回的JSON格式", str(context.exception))

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_empty_markdown(self, mock_llm):
        """Test extract_visa_fields with empty markdown"""
        empty_fields = {
            "Application Information": {
                "visa_type": None,
                "journey_type": None
            }
        }
        
        mock_response = Mock()
        mock_response.content = json.dumps(empty_fields)
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields("")
        
        self.assertEqual(result, empty_fields)
        mock_llm.invoke.assert_called_once()

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_prompt_template(self, mock_llm):
        """Test that prompt template is correctly formatted"""
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_fields)
        mock_llm.invoke.return_value = mock_response
        
        test_text = "Test document content"
        extract_visa_fields(test_text)
        
        # Verify prompt contains the text
        call_args = mock_llm.invoke.call_args[0][0]
        self.assertIn(test_text, call_args)
        self.assertIn("请根据以下文本内容提取相应签证字段", call_args)

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_complex_nested_structure(self, mock_llm):
        """Test extract_visa_fields with complex nested JSON structure"""
        complex_fields = {
            "Application Information": {
                "visa_type": "Long Stay (D)",
                "journey_type": "Multiple"
            },
            "Family Information": {
                "spouse_details": {
                    "surname": "Smith",
                    "forenames": "Jane",
                    "date_of_birth": "1992-05-15"
                },
                "children_details": [
                    {
                        "surname": "Doe",
                        "forename": "Alice",
                        "date_of_birth": "2015-03-20"
                    }
                ]
            }
        }
        
        mock_response = Mock()
        mock_response.content = json.dumps(complex_fields, ensure_ascii=False)
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        self.assertEqual(result, complex_fields)
        self.assertIn("children_details", result["Family Information"])
        self.assertEqual(len(result["Family Information"]["children_details"]), 1)

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_whitespace_handling(self, mock_llm):
        """Test extract_visa_fields handles whitespace in response"""
        # Response with extra whitespace
        json_with_whitespace = f"   \n{json.dumps(self.sample_fields)}\n   "
        mock_response = Mock()
        mock_response.content = json_with_whitespace
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Should handle whitespace correctly
        self.assertEqual(result, self.sample_fields)

    def test_irish_visa_template_prompt_structure(self):
        """Test that the prompt template has correct structure"""
        # Check that template contains key sections
        self.assertIn("爱尔兰签证材料字段识别专家", irish_visa_template_prompt)
        self.assertIn("Application Information", irish_visa_template_prompt)
        self.assertIn("Personal Information", irish_visa_template_prompt)
        self.assertIn("Passport Information", irish_visa_template_prompt)
        self.assertIn("{text}", irish_visa_template_prompt)
        
        # Test formatting
        test_text = "Sample text"
        formatted = irish_visa_template_prompt.format(text=test_text)
        self.assertIn(test_text, formatted)
        self.assertNotIn("{text}", formatted)

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_multiline_json(self, mock_llm):
        """Test extract_visa_fields with multiline JSON"""
        multiline_json = """{
            "Application Information": {
                "visa_type": "Long Stay (D)"
            }
        }"""
        
        mock_response = Mock()
        mock_response.content = multiline_json
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        # Should parse multiline JSON correctly
        self.assertIn("Application Information", result)
        self.assertEqual(result["Application Information"]["visa_type"], "Long Stay (D)")

    @patch('llm_analysis.llm')
    def test_extract_visa_fields_unicode_characters(self, mock_llm):
        """Test extract_visa_fields handles unicode characters"""
        fields_with_unicode = {
            "Personal Information": {
                "surname": "张",
                "forename": "三",
                "place_of_birth": "北京市"
            }
        }
        
        mock_response = Mock()
        mock_response.content = json.dumps(fields_with_unicode, ensure_ascii=False)
        mock_llm.invoke.return_value = mock_response
        
        result = extract_visa_fields(self.sample_markdown)
        
        self.assertEqual(result, fields_with_unicode)
        self.assertEqual(result["Personal Information"]["surname"], "张")


if __name__ == '__main__':
    unittest.main()

