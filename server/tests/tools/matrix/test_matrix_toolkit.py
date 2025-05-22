import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.matrix.toolkit import MatrixToolkit
# Mock the actual tool classes
from jarvis.tools.matrix import send_message

class TestMatrixToolkit(unittest.TestCase):

    @patch('jarvis.tools.matrix.toolkit.MatrixSendMessageTool', spec=send_message.MatrixSendMessageTool)
    def test_get_tools(self, MockMatrixSendMessageTool):
        
        mock_send_message_instance = MockMatrixSendMessageTool.return_value
        
        toolkit = MatrixToolkit()
        tools = toolkit.get_tools()

        self.assertEqual(len(tools), 1)
        MockMatrixSendMessageTool.assert_called_once()
        self.assertIn(mock_send_message_instance, tools)

if __name__ == '__main__':
    unittest.main()
