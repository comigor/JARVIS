import unittest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import os
import sys
import json

# Ensure imports from jarvis are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from jarvis.graph.compressor_chain import (
    retrieve_filtered_chat_history,
    get_summary,
    persist_history,
    summaries_cache, # For clearing cache during tests
)
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.messages.utils import messages_to_dict # For creating test data

class TestCompressorChain(unittest.IsolatedAsyncioTestCase):

    def tearDown(self):
        # Clear the cache after each test to ensure test isolation
        summaries_cache.clear()

    @patch.dict(os.environ, {"MESSAGE_HISTORY_COUNT": "5"})
    @patch("jarvis.graph.compressor_chain.messages_from_dict")
    @patch("builtins.open", new_callable=mock_open)
    async def test_retrieve_filtered_chat_history_with_file(self, mock_file, mock_messages_from_dict):
        mock_file.return_value.read.return_value = '[]' # Mock reading an empty list
        mock_messages_from_dict.return_value = [HumanMessage(content="test")] * 10
        
        history = await retrieve_filtered_chat_history()
        
        mock_file.assert_called_once_with("chat_history.json", "r")
        mock_messages_from_dict.assert_called_once()
        self.assertEqual(len(history), 5) # MESSAGE_HISTORY_COUNT is 5

    @patch.dict(os.environ, {"MESSAGE_HISTORY_COUNT": "0"})
    async def test_retrieve_filtered_chat_history_no_history_count(self):
        history = await retrieve_filtered_chat_history()
        self.assertEqual(len(history), 0)

    @patch.dict(os.environ, {"MESSAGE_HISTORY_COUNT": "5"})
    @patch("builtins.open", side_effect=FileNotFoundError) # Simulate file not existing
    async def test_retrieve_filtered_chat_history_file_not_found(self, mock_file):
        history = await retrieve_filtered_chat_history()
        self.assertEqual(len(history), 0)
        mock_file.assert_called_once_with("chat_history.json", "r")

    @patch("jarvis.graph.compressor_chain._call_llm", new_callable=AsyncMock)
    async def test_get_summary_no_cache(self, mock_call_llm):
        mock_llm = MagicMock()
        mock_call_llm.return_value = AIMessage(content="Summary content")
        
        test_history = [HumanMessage(content="Hello")]
        config = {"configurable": {"session_id": "test_session"}}
        
        summary_messages = await get_summary(mock_llm, test_history, config)
        
        self.assertEqual(len(summary_messages), 1)
        self.assertIsInstance(summary_messages[0], SystemMessage)
        self.assertIn("Summary content", summary_messages[0].content)
        mock_call_llm.assert_called_once_with(mock_llm, test_history, config)
        self.assertIn("test_session", summaries_cache)

    @patch("jarvis.graph.compressor_chain._call_llm", new_callable=AsyncMock)
    async def test_get_summary_with_cache(self, mock_call_llm):
        mock_llm = MagicMock()
        
        session_id = "test_session_cache"
        cached_summary = [SystemMessage(content="Cached summary")]
        summaries_cache[session_id] = cached_summary
        
        test_history = [HumanMessage(content="Hello again")]
        config = {"configurable": {"session_id": session_id}}
        
        summary_messages = await get_summary(mock_llm, test_history, config)
        
        self.assertEqual(summary_messages, cached_summary)
        mock_call_llm.assert_not_called() # Should use cache

    async def test_get_summary_empty_history(self):
        mock_llm = MagicMock()
        summary_messages = await get_summary(mock_llm, [], None)
        self.assertEqual(len(summary_messages), 0)

    @patch("jarvis.graph.compressor_chain.messages_to_dict")
    @patch("builtins.open", new_callable=mock_open)
    async def test_persist_history(self, mock_file, mock_messages_to_dict):
        history_to_persist: List[BaseMessage] = [
            HumanMessage(content="User message 1"),
            AIMessage(content="AI response 1"),
            HumanMessage(content="User message 1"), # Duplicate
            AIMessage(content="AI response with tool", tool_calls=[{"id": "1", "name": "t", "args": {}}]), # Tool call
            SystemMessage(content="System info") # Should be filtered out
        ]
        
        expected_filtered_for_persistence = [
            history_to_persist[0], # HumanMessage
            history_to_persist[1], # AIMessage (no tool calls)
        ]
        
        # This mock is for the final list that gets converted
        mock_messages_to_dict.return_value = messages_to_dict(expected_filtered_for_persistence)

        await persist_history(history_to_persist)

        # Check that messages_to_dict was called with the correctly filtered and deduped list
        args_list = mock_messages_to_dict.call_args[0][0] # First arg of first call
        self.assertEqual(len(args_list), 2)
        self.assertEqual(args_list[0].content, "User message 1")
        self.assertEqual(args_list[1].content, "AI response 1")
        
        # Check that file was written
        mock_file.assert_called_once_with("chat_history.json", "w")
        mock_file().write.assert_called_once_with(json.dumps(messages_to_dict(expected_filtered_for_persistence)))

if __name__ == '__main__':
    unittest.main()
