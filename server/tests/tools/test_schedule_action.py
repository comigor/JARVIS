import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from jarvis.tools.schedule_action import ScheduleActionTool, ScheduleActionInput

class TestScheduleActionTool(unittest.TestCase):

    @patch('jarvis.tools.schedule_action.httpx.Client')
    @patch('jarvis.tools.schedule_action.BackgroundScheduler')
    def test_run_schedules_action_and_executes(self, MockBackgroundScheduler, MockHttpxClient):
        # Setup mocks
        mock_scheduler_instance = MockBackgroundScheduler.return_value
        mock_httpx_instance = MockHttpxClient.return_value
        
        # Mock the response from the httpx post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": "action executed"}
        mock_httpx_instance.post.return_value = mock_response

        tool = ScheduleActionTool()
        # Replace the tool's scheduler instance with our mock
        tool.scheduler = mock_scheduler_instance 
        tool.client = mock_httpx_instance

        test_moment = datetime.now() + timedelta(seconds=10)
        test_instructions = "Test instructions"

        result = tool._run(moment=test_moment, instructions=test_instructions)

        self.assertEqual(result, f"The action \"{test_instructions}\" has been scheduled to run at {test_moment}.")
        
        # Verify scheduler.add_job was called
        mock_scheduler_instance.add_job.assert_called_once()
        args, kwargs = mock_scheduler_instance.add_job.call_args
        
        self.assertEqual(kwargs['trigger'], 'date')
        self.assertEqual(kwargs['next_run_time'], test_moment)
        
        # Simulate the execution of the scheduled job
        scheduled_func = args[0] # The first positional argument to add_job is 'func'
        
        # Call the scheduled function
        job_execution_result = scheduled_func()
        
        # Verify httpx client was called correctly
        mock_httpx_instance.post.assert_called_once_with(
            "http://192.168.10.20:10055/invoke",
            json={
                "input": test_instructions,
                "config": {"configurable": {"session_id": unittest.mock.ANY}}, # session_id is a uuid
            },
        )
        self.assertIn("action executed", job_execution_result) # Check if the mocked response is part of the result

    @patch('jarvis.tools.schedule_action.httpx.Client')
    @patch('jarvis.tools.schedule_action.BackgroundScheduler')
    def test_run_schedules_action_httpx_error(self, MockBackgroundScheduler, MockHttpxClient):
        mock_scheduler_instance = MockBackgroundScheduler.return_value
        mock_httpx_instance = MockHttpxClient.return_value
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_httpx_instance.post.return_value = mock_response

        tool = ScheduleActionTool()
        tool.scheduler = mock_scheduler_instance
        tool.client = mock_httpx_instance

        test_moment = datetime.now() + timedelta(seconds=10)
        test_instructions = "Error instructions"

        result = tool._run(moment=test_moment, instructions=test_instructions)
        self.assertEqual(result, f"The action \"{test_instructions}\" has been scheduled to run at {test_moment}.")
        
        args, _ = mock_scheduler_instance.add_job.call_args
        scheduled_func = args[0]
        job_execution_result = scheduled_func()
        
        self.assertIn("Sorry, I can't do that (got error 500)", job_execution_result)

if __name__ == '__main__':
    unittest.main()
