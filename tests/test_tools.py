'''
This code provides unit tests for the Fax.Plus integration with LangChain. 
Here's what's included:

Test Setup:
- Mocks the environment variables for Fax.Plus credentials
- Creates a temporary PDF file for testing fax sending

FaxSenderTool Tests:
- Tests successful fax sending with proper parameters
- Tests handling of invalid fax numbers
- Tests handling of non-existent files

FaxStatusTool Tests:
- Tests retrieval of fax status from the API
- Verifies correct parsing of status, cost, and page count

FaxHistoryTool Tests:
- Tests retrieval of fax history
- Verifies proper handling of multiple fax records

The tests use Python's unittest framework with mocking, to avoid making actual 
API calls during testing. This approach lets you verify your tools work 
correctly without sending real faxes or requiring actual credentials during testing.

To run these tests, you can use:
bashCopypython -m unittest tests/test_tools.py

'''

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile

from langchain_fax.tools import FaxSenderTool, FaxStatusTool, FaxHistoryTool


class TestFaxTools(unittest.TestCase):
    """Test cases for Fax.Plus LangChain tools."""

    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            "FAXPLUS_ACCESS_TOKEN": "mock_token",
            "FAXPLUS_USER_ID": "mock_user_id"
        })
        self.env_patcher.start()
        
        # Create a temporary PDF file for testing
        self.temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_pdf.write(b"%PDF-1.4\n%Test PDF content")
        self.temp_pdf.close()
        
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        if os.path.exists(self.temp_pdf.name):
            os.unlink(self.temp_pdf.name)

    @patch('faxplus.Configuration')
    @patch('faxplus.FaxApi')
    def test_fax_sender_tool(self, mock_fax_api, mock_config):
        """Test the FaxSenderTool functionality."""
        # Set up mocks
        mock_fax_instance = MagicMock()
        mock_fax_api.return_value = mock_fax_instance
        mock_fax_instance.send_fax.return_value = MagicMock(fax_id="mock_fax_id")
        
        # Create and test the tool
        tool = FaxSenderTool()
        
        # Test successful fax sending
        result = tool.run({
            "fax_number": "+12025550123",
            "file_path": self.temp_pdf.name,
            "subject": "Test Fax"
        })
        
        # Verify the tool called the API correctly
        mock_fax_instance.send_fax.assert_called_once()
        self.assertIn("successfully sent", result)
        self.assertIn("mock_fax_id", result)
    
    @patch('faxplus.Configuration')
    @patch('faxplus.FaxApi')
    def test_fax_status_tool(self, mock_fax_api, mock_config):
        """Test the FaxStatusTool functionality."""
        # Set up mocks
        mock_fax_instance = MagicMock()
        mock_fax_api.return_value = mock_fax_instance
        mock_fax = MagicMock()
        mock_fax.status = "success"
        mock_fax.cost = 1
        mock_fax.direction = "outbound"
        mock_fax.page_count = 2
        mock_fax_instance.get_fax.return_value = mock_fax
        
        # Create and test the tool
        tool = FaxStatusTool()
        
        # Test fax status retrieval
        result = tool.run({"fax_id": "mock_fax_id"})
        
        # Verify the tool called the API correctly
        mock_fax_instance.get_fax.assert_called_once_with("mock_fax_id")
        self.assertIn("success", result)
        self.assertIn("2 pages", result)
    
    @patch('faxplus.Configuration')
    @patch('faxplus.AccountApi')
    def test_fax_history_tool(self, mock_account_api, mock_config):
        """Test the FaxHistoryTool functionality."""
        # Set up mocks
        mock_account_instance = MagicMock()
        mock_account_api.return_value = mock_account_instance
        
        # Create mock fax records
        mock_fax1 = MagicMock()
        mock_fax1.id = "fax_id_1"
        mock_fax1.status = "success"
        mock_fax1.to = "+12025550123"
        mock_fax1.date = "2023-01-01T12:00:00Z"
        
        mock_fax2 = MagicMock()
        mock_fax2.id = "fax_id_2"
        mock_fax2.status = "failed"
        mock_fax2.to = "+12025550456"
        mock_fax2.date = "2023-01-02T12:00:00Z"
        
        mock_account_instance.get_fax_list.return_value = MagicMock(
            data=[mock_fax1, mock_fax2]
        )
        
        # Create and test the tool
        tool = FaxHistoryTool()
        
        # Test fax history retrieval
        result = tool.run({"limit": 2})
        
        # Verify the tool called the API correctly
        mock_account_instance.get_fax_list.assert_called_once()
        self.assertIn("fax_id_1", result)
        self.assertIn("fax_id_2", result)
        self.assertIn("success", result)
        self.assertIn("failed", result)

    @patch('faxplus.Configuration')
    @patch('faxplus.FaxApi')
    def test_invalid_fax_number(self, mock_fax_api, mock_config):
        """Test handling of invalid fax numbers."""
        # Set up mocks
        mock_fax_instance = MagicMock()
        mock_fax_api.return_value = mock_fax_instance
        mock_fax_instance.send_fax.side_effect = Exception("Invalid fax number")
        
        # Create and test the tool
        tool = FaxSenderTool()
        
        # Test with invalid fax number
        with self.assertRaises(Exception):
            tool.run({
                "fax_number": "invalid-number",
                "file_path": self.temp_pdf.name,
                "subject": "Test Fax"
            })

    @patch('faxplus.Configuration')
    @patch('faxplus.FaxApi')
    def test_nonexistent_file(self, mock_fax_api, mock_config):
        """Test handling of non-existent files."""
        # Create and test the tool
        tool = FaxSenderTool()
        
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            tool.run({
                "fax_number": "+12025550123",
                "file_path": "nonexistent_file.pdf",
                "subject": "Test Fax"
            })


if __name__ == "__main__":
    unittest.main()