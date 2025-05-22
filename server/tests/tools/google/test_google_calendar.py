import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import os
import sys

# Ensure imports from jarvis.tools are possible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from jarvis.tools.google.calendar import ListEventsTool, CreateEventTool

class TestGoogleCalendarTools(unittest.TestCase):

    @patch('jarvis.tools.google.calendar.authenticate_with_google')
    @patch('jarvis.tools.google.calendar.build')
    def test_list_events_tool(self, MockBuild, MockAuthenticate):
        # Setup mocks
        mock_creds = MagicMock()
        MockAuthenticate.return_value = mock_creds
        
        mock_service = MagicMock()
        MockBuild.return_value = mock_service
        
        mock_events_result = MagicMock()
        mock_events_result.get.return_value = [{"summary": "Test Event"}]
        mock_service.events.return_value.list.return_value.execute.return_value = mock_events_result

        tool = ListEventsTool()
        
        from_dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        to_dt = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
        
        result = tool._run(from_datetime=from_dt, to_datetime=to_dt)

        self.assertIn("Test Event", result)
        MockAuthenticate.assert_called_once()
        MockBuild.assert_called_once_with("calendar", "v3", credentials=mock_creds)
        mock_service.events.return_value.list.assert_called_once_with(
            calendarId="primary",
            timeMin=from_dt.isoformat(),
            timeMax=to_dt.isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )

    @patch('jarvis.tools.google.calendar.authenticate_with_google')
    @patch('jarvis.tools.google.calendar.build')
    def test_create_event_tool(self, MockBuild, MockAuthenticate):
        # Setup mocks
        mock_creds = MagicMock()
        MockAuthenticate.return_value = mock_creds
        
        mock_service = MagicMock()
        MockBuild.return_value = mock_service
        
        mock_created_event = {"summary": "New Event", "id": "123"}
        mock_service.events.return_value.insert.return_value.execute.return_value = mock_created_event

        tool = CreateEventTool()
        
        summary = "New Event"
        start_dt = datetime(2024, 1, 2, 14, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2024, 1, 2, 15, 0, 0, tzinfo=timezone.utc)
        location = "Test Location"
        
        result = tool._run(summary=summary, start_datetime=start_dt, end_datetime=end_dt, location=location)

        self.assertIn("New Event", result)
        self.assertIn("123", result)
        MockAuthenticate.assert_called_once()
        MockBuild.assert_called_once_with("calendar", "v3", credentials=mock_creds)
        
        expected_event_body = {
            "summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
            "location": location,
        }
        mock_service.events.return_value.insert.assert_called_once_with(
            calendarId="primary", body=expected_event_body
        )

if __name__ == '__main__':
    unittest.main()
