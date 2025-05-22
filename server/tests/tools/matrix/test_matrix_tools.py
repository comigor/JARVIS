import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
import asyncio

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.matrix.send_message import MatrixSendMessageTool
from nio import RoomSendResponse, RoomSendError # For type checking mock

class TestMatrixTools(unittest.IsolatedAsyncioTestCase): # Use IsolatedAsyncioTestCase for async tests

    @patch('jarvis.tools.matrix.send_message.client', new_callable=AsyncMock) # Mock the client from base
    async def test_matrix_send_message_tool_success(self, mock_matrix_client):
        # Setup mock client behavior
        mock_room_info = {"id": "!fakeroom:matrix.org"}
        mock_matrix_client.find_room_id_by_name.return_value = mock_room_info
        
        # Mock the send_message response
        mock_send_response = MagicMock(spec=RoomSendResponse) # Or just MagicMock() if type is not critical
        mock_matrix_client.send_message.return_value = mock_send_response

        tool = MatrixSendMessageTool()
        
        room_name = "Test Room"
        message = "Hello Matrix!"
        
        result = await tool._arun(room_name=room_name, message=message)
        
        self.assertEqual(result, "Message sent successfully.")
        mock_matrix_client.find_room_id_by_name.assert_called_once_with(room_name)
        mock_matrix_client.send_message.assert_called_once_with(mock_room_info["id"], message)

    @patch('jarvis.tools.matrix.send_message.client', new_callable=AsyncMock)
    async def test_matrix_send_message_tool_room_not_found(self, mock_matrix_client):
        mock_matrix_client.find_room_id_by_name.return_value = None # Simulate room not found

        tool = MatrixSendMessageTool()
        
        result = await tool._arun(room_name="Unknown Room", message="Test")
        
        self.assertEqual(result, "Sorry, I can't do that.") # Or a more specific error if the tool returns one
        mock_matrix_client.find_room_id_by_name.assert_called_once_with("Unknown Room")
        mock_matrix_client.send_message.assert_not_called()

    @patch('jarvis.tools.matrix.send_message.client', new_callable=AsyncMock)
    async def test_matrix_send_message_tool_send_error(self, mock_matrix_client):
        mock_room_info = {"id": "!fakeroom:matrix.org"}
        mock_matrix_client.find_room_id_by_name.return_value = mock_room_info
        
        # Simulate a RoomSendError or just a non-RoomSendResponse
        mock_matrix_client.send_message.return_value = MagicMock(spec=RoomSendError) 

        tool = MatrixSendMessageTool()
        
        result = await tool._arun(room_name="Test Room", message="Test")
        
        self.assertEqual(result, "Sorry, I can't do that.")
        mock_matrix_client.send_message.assert_called_once()

    @patch('jarvis.tools.matrix.send_message.client', None) # Simulate client is None
    async def test_matrix_send_message_tool_no_client(self, ): # Parameter name must be different or removed
        tool = MatrixSendMessageTool()
        result = await tool._arun(room_name="Test Room", message="Test")
        self.assertEqual(result, "Sorry, I can't do that.")


if __name__ == '__main__':
    unittest.main()
