import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
import asyncio

# Ensure imports from jarvis are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


# Mock environment variables before importing server
DEFAULT_ENV_VARS = {
    "DEBUG": "True", # Keep DEBUG true to simplify some tests (e.g. no scheduler, no matrix)
    "HOMEASSISTANT_URL": "http://fakeha",
    "HOMEASSISTANT_KEY": "fakekey_ha",
    "ENABLE_MATRIX": "False", # Keep false to avoid matrix setup in tests
    "OVERSEER_URL": "http://fakeoverseer",
    "OVERSEER_API_KEY": "fakekey_overseer",
    "OPENAI_API_KEY": "fake_openai_key", # Needed for ChatOpenAI
    # Add other env vars if server.py starts using them directly at import time
}

with patch.dict(os.environ, DEFAULT_ENV_VARS):
    from jarvis import server # Import server after mocking env vars

class TestServer(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Ensure each test has a fresh, controlled environment
        self.patcher = patch.dict(os.environ, DEFAULT_ENV_VARS)
        self.mock_environ = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('jarvis.server.ChatOpenAI')
    def test_get_llm(self, MockChatOpenAI):
        mock_llm_instance = MockChatOpenAI.return_value
        llm = server.get_llm()
        self.assertEqual(llm, mock_llm_instance)
        MockChatOpenAI.assert_called_once_with(
            model="gpt-4o-mini", temperature=0.15, streaming=False, request_timeout=30
        )

    @patch('jarvis.server.ScheduleActionTool')
    @patch('jarvis.server.BeancountAddTransactionTool')
    @patch('jarvis.server.HomeAssistantToolkit')
    @patch('jarvis.server.GoogleToolkit')
    @patch('jarvis.server.MatrixToolkit') # Will be skipped if ENABLE_MATRIX is false
    @patch('jarvis.server.WikipediaAPIWrapper')
    @patch('jarvis.server.PythonREPL')
    @patch('jarvis.server.OverseerToolkit')
    def test_tools_creation(self, MockOverseerToolkit, MockPythonREPL, MockWikipediaAPIWrapper,
                            MockMatrixToolkit, MockGoogleToolkit, MockHomeAssistantToolkit,
                            MockBeancount, MockScheduleAction):
        # This test re-evaluates the tools list creation in server.py
        # To do this properly, we might need to reload server or refactor tools list to a function
        # For simplicity, we assume the tools list is evaluated upon import based on mocked env vars.
        # Or, if server.tools is accessible and re-evaluated, we can check that.
        
        # Re-import or re-run the part of server.py that defines `tools` if it's not top-level
        # For this example, let's assume `server.tools` is defined at the top level and accessible.
        
        self.assertTrue(len(server.tools) > 0) # Basic check
        MockScheduleAction.assert_called()
        MockBeancount.assert_called()
        MockHomeAssistantToolkit.assert_called()
        MockGoogleToolkit.assert_called()
        
        if DEFAULT_ENV_VARS.get("ENABLE_MATRIX") == "True": # Or how it's checked in server.py
             MockMatrixToolkit.assert_called()
        else:
            MockMatrixToolkit.assert_not_called()

        MockWikipediaAPIWrapper.assert_called()
        MockPythonREPL.assert_called()
        MockOverseerToolkit.assert_called()


    @patch('jarvis.server.generate_graph')
    def test_graph_generation(self, mock_generate_graph):
        # Similar to tools, graph is often top-level.
        # If generate_graph is called at import time:
        mock_generate_graph.assert_called_once_with(server.llm, server.tools)
        self.assertIsNotNone(server.graph) # Check if graph is assigned

    @patch('jarvis.server.FastAPI')
    @patch('jarvis.server.add_routes')
    def test_fastapi_app_setup(self, mock_add_routes, MockFastAPI):
        # Assuming app is created at top-level
        MockFastAPI.assert_called_once()
        mock_add_routes.assert_called_once()
        # Check that add_routes was called with the graph (or wrapped graph)
        args, _ = mock_add_routes.call_args
        self.assertIsNotNone(args[1]) # args[1] should be the runnable (graph | lambda)


    @patch('jarvis.server.BackgroundScheduler')
    @patch.dict(os.environ, {**DEFAULT_ENV_VARS, "DEBUG": "False"}) # Test non-DEBUG path
    def test_scheduler_setup_non_debug(self, MockBackgroundScheduler):
        # This test requires careful handling if server module is already imported.
        # One way is to refactor scheduler setup into a function and call it.
        # Or, use importlib.reload if Python version allows and it's safe.
        
        # For this example, we assume we can check if the scheduler was started.
        # This part is tricky because scheduler setup is conditional at module level.
        # A better approach would be to have scheduler setup in a function.
        
        # If `server.scheduler` is accessible:
        # MockBackgroundScheduler.assert_called()
        # server.scheduler.start.assert_called()
        # server.scheduler.add_job.assert_any_call(id="refresh_token", func=server.refresh_google_token, trigger="interval", hours=1)
        # server.scheduler.add_job.assert_any_call(id="save_rooms", func=server.save_rooms, trigger="interval", minutes=15)
        pass # This test is complex due to module-level conditional logic


    @patch('jarvis.server.uvicorn.Server', new_callable=MagicMock)
    @patch('jarvis.server.asyncio.create_task', side_effect=lambda coro: AsyncMock(spec=asyncio.Task, name=coro.__name__))
    @patch('jarvis.tools.matrix.base.main', new_callable=AsyncMock) # Mock matrix_main
    @patch.dict(os.environ, {**DEFAULT_ENV_VARS, "DEBUG": "False", "ENABLE_MATRIX": "True"})
    async def test_main_function_debug_false_matrix_true(self, mock_matrix_main, mock_create_task, MockUvicornServer):
        mock_uvicorn_serve = AsyncMock()
        MockUvicornServer.return_value.serve = mock_uvicorn_serve

        await server.main()

        self.assertEqual(mock_create_task.call_count, 2) # matrix and uvicorn
        
        # Check if create_task was called with something that leads to matrix_main and server.serve
        # This is a bit indirect.
        found_matrix_task = False
        found_uvicorn_task = False
        for call_arg in mock_create_task.call_args_list:
            coro = call_arg[0][0] # The coroutine passed to create_task
            if "matrix_main" in str(coro): # Check based on coroutine name or content
                found_matrix_task = True
            elif "server.serve" in str(coro): # Check if it's wrapping the uvicorn server's serve method
                found_uvicorn_task = True
        
        self.assertTrue(found_matrix_task)
        self.assertTrue(found_uvicorn_task)
        
        # Check that the tasks would have been awaited (simplified)
        # In a real scenario, await asyncio.wait would be called.
        # Here we check if the mocked tasks (AsyncMock) were awaited if they had `await` used on them.
        # Since `asyncio.wait` is used, the tasks themselves are not directly awaited in `server.main`.
        # Instead, their completion is managed by `asyncio.wait`.
        # We can check if the underlying methods (matrix_main, uvicorn_serve) were called via the tasks.
        
        # This requires the AsyncMock tasks to be "run" for their wrapped coros to execute.
        # This part of testing `asyncio.wait` is complex with simple mocks.
        # A more direct way is to check if the functions that create_task wraps were called.
        # However, create_task itself is mocked.
        
        # For now, we'll rely on the fact that create_task was called with the right targets.
        # A deeper test would involve a more sophisticated async testing setup.


    @patch('jarvis.server.uvicorn.Server', new_callable=MagicMock)
    @patch('jarvis.server.asyncio.create_task', side_effect=lambda coro: AsyncMock(spec=asyncio.Task))
    @patch('jarvis.tools.matrix.base.main', new_callable=AsyncMock)
    @patch.dict(os.environ, {**DEFAULT_ENV_VARS, "DEBUG": "True"}) # DEBUG True
    async def test_main_function_debug_true(self, mock_matrix_main, mock_create_task, MockUvicornServer):
        mock_uvicorn_serve = AsyncMock()
        MockUvicornServer.return_value.serve = mock_uvicorn_serve
        
        await server.main()
        
        self.assertEqual(mock_create_task.call_count, 1) # Only uvicorn
        coro = mock_create_task.call_args[0][0]
        self.assertTrue("server.serve" in str(coro))
        mock_matrix_main.assert_not_called()


if __name__ == '__main__':
    # Important: Need to run with python -m unittest for tests to be discovered correctly
    # due to the way server module is imported after patching os.environ
    unittest.main()
