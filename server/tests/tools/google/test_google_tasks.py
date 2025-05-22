import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.google.tasks import ListTasksTool, CreateTaskTool

class TestGoogleTasksTools(unittest.TestCase):

    @patch('jarvis.tools.google.tasks.authenticate_with_google')
    @patch('jarvis.tools.google.tasks.build')
    def test_list_tasks_tool(self, MockBuild, MockAuthenticate):
        # Setup mocks
        mock_creds = MagicMock()
        MockAuthenticate.return_value = mock_creds
        
        mock_service = MagicMock()
        MockBuild.return_value = mock_service
        
        # Mock the task lists response
        mock_task_lists_response = {"items": [{"id": "default_list_id"}]}
        mock_service.tasklists.return_value.list.return_value.execute.return_value = mock_task_lists_response
        
        mock_tasks_result = MagicMock()
        mock_tasks_result.get.return_value = [{"title": "Test Task"}]
        mock_service.tasks.return_value.list.return_value.execute.return_value = mock_tasks_result

        tool = ListTasksTool()
        
        from_dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        to_dt = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        
        result = tool._run(from_datetime=from_dt, to_datetime=to_dt, show_completed=True)

        self.assertIn("Test Task", result)
        MockAuthenticate.assert_called_once()
        MockBuild.assert_called_once_with("tasks", "v1", credentials=mock_creds)
        
        # service.tasklists().list().execute() is called implicitly in _run if not handled
        # In this version of the code, it is called to get default_tasklist_id, but then it's overridden.
        # We can simplify by assuming default_tasklist_id = "@default" as in the code.
        
        mock_service.tasks.return_value.list.assert_called_once_with(
            tasklist="@default", # The code overrides to "@default"
            dueMin=from_dt.isoformat(),
            dueMax=to_dt.isoformat(),
            showCompleted=True,
            showDeleted=False, # Default
            showHidden=False,  # Default
        )

    @patch('jarvis.tools.google.tasks.authenticate_with_google')
    @patch('jarvis.tools.google.tasks.build')
    def test_create_task_tool(self, MockBuild, MockAuthenticate):
        # Setup mocks
        mock_creds = MagicMock()
        MockAuthenticate.return_value = mock_creds
        
        mock_service = MagicMock()
        MockBuild.return_value = mock_service

        # Mock the task lists response
        mock_task_lists_response = {"items": [{"id": "default_list_id"}]}
        mock_service.tasklists.return_value.list.return_value.execute.return_value = mock_task_lists_response
        
        mock_created_task = {"title": "New Task", "id": "task123"}
        mock_service.tasks.return_value.insert.return_value.execute.return_value = mock_created_task

        tool = CreateTaskTool()
        
        task_title = "New Task"
        due_dt = datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        
        result = tool._run(task_title=task_title, due_datetime=due_dt)

        self.assertIn("New Task", result)
        self.assertIn("task123", result)
        MockAuthenticate.assert_called_once()
        MockBuild.assert_called_once_with("tasks", "v1", credentials=mock_creds)
        
        expected_task_body = {
            "title": task_title,
            "due": due_dt.isoformat(),
        }
        mock_service.tasks.return_value.insert.assert_called_once_with(
            tasklist="@default", body=expected_task_body # The code overrides to "@default"
        )

if __name__ == '__main__':
    unittest.main()
