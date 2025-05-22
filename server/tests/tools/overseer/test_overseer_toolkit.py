import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.overseer.toolkit import OverseerToolkit
# Mock the actual tool classes
from jarvis.tools.overseer import search, request

class TestOverseerToolkit(unittest.TestCase):

    @patch('jarvis.tools.overseer.toolkit.OverseerSearchTool', spec=search.OverseerSearchTool)
    @patch('jarvis.tools.overseer.toolkit.OverseerDownloadTool', spec=request.OverseerDownloadTool)
    def test_get_tools(self, MockOverseerDownloadTool, MockOverseerSearchTool):
        
        mock_search_instance = MockOverseerSearchTool.return_value
        mock_download_instance = MockOverseerDownloadTool.return_value
        
        api_key = "test_key"
        base_url = "http://test_url"
        
        toolkit = OverseerToolkit(api_key=api_key, base_url=base_url)
        tools = toolkit.get_tools()

        self.assertEqual(len(tools), 2)

        MockOverseerSearchTool.assert_called_once_with(base_url=base_url, api_key=api_key)
        MockOverseerDownloadTool.assert_called_once_with(base_url=base_url, api_key=api_key)

        self.assertIn(mock_search_instance, tools)
        self.assertIn(mock_download_instance, tools)

if __name__ == '__main__':
    unittest.main()
