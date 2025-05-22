import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.google.toolkit import GoogleToolkit
# We will mock the actual tool classes to simplify toolkit testing
from jarvis.tools.google import calendar as google_calendar
from jarvis.tools.google import tasks as google_tasks
from langchain_google_community import GoogleSearchRun

class TestGoogleToolkit(unittest.TestCase):

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key", "GOOGLE_CSE_ID": "test_cse_id"})
    @patch('jarvis.tools.google.toolkit.GoogleSearchRun', spec=GoogleSearchRun)
    @patch('jarvis.tools.google.toolkit.calendar.ListEventsTool', spec=google_calendar.ListEventsTool)
    @patch('jarvis.tools.google.toolkit.calendar.CreateEventTool', spec=google_calendar.CreateEventTool)
    @patch('jarvis.tools.google.toolkit.tasks.ListTasksTool', spec=google_tasks.ListTasksTool)
    @patch('jarvis.tools.google.toolkit.tasks.CreateTaskTool', spec=google_tasks.CreateTaskTool)
    def test_get_tools(self, MockCreateTask, MockListTasks, MockCreateEvent, MockListEvents, MockGoogleSearch):
        
        mock_search_instance = MockGoogleSearch.return_value
        mock_list_events_instance = MockListEvents.return_value
        mock_create_event_instance = MockCreateEvent.return_value
        mock_list_tasks_instance = MockListTasks.return_value
        mock_create_task_instance = MockCreateTask.return_value

        toolkit = GoogleToolkit()
        tools = toolkit.get_tools()

        self.assertEqual(len(tools), 5)

        # Check that constructor for GoogleSearchRun was called correctly
        MockGoogleSearch.assert_called_once()
        call_args = MockGoogleSearch.call_args
        self.assertIsNotNone(call_args.kwargs.get('api_wrapper'))
        # Further checks on api_wrapper args if necessary, but that's GoogleSearchAPIWrapper's job

        # Check that tools are instantiated
        MockListEvents.assert_called_once()
        MockCreateEvent.assert_called_once()
        MockListTasks.assert_called_once()
        MockCreateTask.assert_called_once()

        # Check if the instances returned by mocks are in the tools list
        self.assertIn(mock_search_instance, tools)
        self.assertIn(mock_list_events_instance, tools)
        self.assertIn(mock_create_event_instance, tools)
        self.assertIn(mock_list_tasks_instance, tools)
        self.assertIn(mock_create_task_instance, tools)


if __name__ == '__main__':
    unittest.main()
