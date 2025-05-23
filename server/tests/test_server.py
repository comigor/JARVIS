import pytest
import os
from unittest.mock import patch, Mock

from jarvis.server import get_llm, aaaaaaaaaaaaaa
from langchain_openai import ChatOpenAI

# Helper class to mock message objects for aaaaaaaaaaaaaa tests
class MockMessage:
    def __init__(self, content):
        self.content = content

# Tests for get_llm()
# Patch os.environ to include OPENAI_API_KEY as it's cleared by clear=True
@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummykey-for-tests"}, clear=True)
def test_get_llm_default_openai():
    """
    Tests that get_llm returns a ChatOpenAI instance by default
    when no specific environment variables (like DEBUG or GROQ_API_KEY) are set,
    ensuring OPENAI_API_KEY is present in the patched env.
    """
    llm = get_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.15

@patch.dict(os.environ, {"DEBUG": "true", "OPENAI_API_KEY": "sk-dummykey-for-tests"}, clear=True)
def test_get_llm_debug_openai():
    """
    Tests that get_llm returns a ChatOpenAI instance even when DEBUG is true,
    as the specific DEBUG logic for a different ChatOpenAI configuration is commented out.
    Ensures OPENAI_API_KEY is present in the patched env.
    """
    llm = get_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0.15


# Tests for aaaaaaaaaaaaaa()
def test_aaaaaaaaaaaaaa_with_messages():
    """
    Tests aaaaaaaaaaaaaa function when the input dictionary has a 'messages' key.
    Uses MockMessage for message content.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {"messages": [MockMessage("test message from messages")]}
        result = aaaaaaaaaaaaaa(input_dict)
        assert result == "test message from messages"
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)

def test_aaaaaaaaaaaaaa_with_persist_messages():
    """
    Tests aaaaaaaaaaaaaa function when 'messages' is not present,
    but 'persist_messages' is. Uses MockMessage.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {"persist_messages": {"messages": [MockMessage("test message from persist")]}}
        result = aaaaaaaaaaaaaa(input_dict)
        assert result == "test message from persist"
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)

def test_aaaaaaaaaaaaaa_messages_takes_precedence():
    """
    Tests aaaaaaaaaaaaaa function when both 'messages' and 'persist_messages' are present.
    'messages' should take precedence. Uses MockMessage.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {
            "messages": [MockMessage("message from messages key")],
            "persist_messages": {"messages": [MockMessage("message from persist key")]}
        }
        result = aaaaaaaaaaaaaa(input_dict)
        assert result == "message from messages key"
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)

def test_aaaaaaaaaaaaaa_empty_persist_messages_fallback():
    """
    Tests aaaaaaaaaaaaaa function when 'messages' is not present,
    and 'persist_messages' is present but its 'messages' list is empty.
    This should raise an IndexError.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {"persist_messages": {"messages": []}}
        with pytest.raises(IndexError):
            aaaaaaaaaaaaaa(input_dict)
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)

def test_aaaaaaaaaaaaaa_missing_keys():
    """
    Tests aaaaaaaaaaaaaa function when neither 'messages' nor 'persist_messages'
    (or its sub-keys) are present. This should result in a TypeError.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {"other_key": "some_value"}
        with pytest.raises(TypeError): # Expects TypeError because None[-1]
            aaaaaaaaaaaaaa(input_dict)
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)

def test_aaaaaaaaaaaaaa_empty_messages_list():
    """
    Tests aaaaaaaaaaaaaa function when 'messages' key is present but the list is empty.
    This should raise an IndexError.
    """
    with patch('jarvis.server._LOGGER') as mock_logger, \
         patch('builtins.print') as mock_print:
        input_dict = {"messages": []}
        with pytest.raises(IndexError):
            aaaaaaaaaaaaaa(input_dict)
        mock_logger.info.assert_called_once_with(input_dict)
        mock_print.assert_called_once_with(input_dict)
