from typing import Type, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from googleapiclient.discovery import build
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from .base import authenticate_with_google
from ..base import BaseAbility
from ..fuckio import async_add_executor_job

class GoogleCalendarEventsSchema(BaseModel):
    from_datetime: datetime = Field(
        description='From which timestamp you want the events (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z)'
    )
    to_datetime: datetime = Field(
        description='To which timestamp you want the events (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z)'
    )

class GoogleCalendarTool(BaseTool):
    name = 'google_calendar_tool'
    description = 'List all events on Google Calendar for a specific time range'
    args_schema: Type[BaseModel] = GoogleCalendarEventsSchema

    async def _arun(self, from_datetime: datetime, to_datetime: datetime):
        creds = await authenticate_with_google()

        # Build the Google Calendar API service
        service = await async_add_executor_job(build, 'calendar', 'v3', credentials=creds)

        # Format the datetime objects to RFC3339
        from_datetime_str = from_datetime.astimezone(timezone.utc).isoformat()
        to_datetime_str = to_datetime.astimezone(timezone.utc).isoformat()

        # Get events for the specified time range
        events_result = service.events().list(
            calendarId='primary',
            timeMin=from_datetime_str,
            timeMax=to_datetime_str,
            maxResults=10,  # You can adjust the number of results as needed
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        
        return events

    def _run(self, from_datetime: datetime, to_datetime: datetime):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

class CreateGoogleCalendarEventSchema(BaseModel):
    summary: str = Field(description='Summary of the event')
    start_datetime: datetime = Field(
        description='The start timestamp, as a combined date-time value (formatted according to RFC3339).'
    )
    end_datetime: datetime = Field(
        description='The end timestamp, as a combined date-time value (formatted according to RFC3339).'
    )
    location: str = Field(
        None,
        description='Geographic location of the event as free-form text. Optional.'
    )

class CreateGoogleCalendarEventTool(BaseTool):
    name = 'create_google_calendar_event_tool'
    description = 'Create an event on Google Calendar'
    args_schema: Type[BaseModel] = CreateGoogleCalendarEventSchema

    async def _arun(self, summary: str, start_datetime: datetime, end_datetime: datetime, location: str):
        creds = await authenticate_with_google()

        # Build the Google Calendar API service
        service = await async_add_executor_job(build, 'calendar', 'v3', credentials=creds)

        # Format the datetime objects to RFC3339
        start_datetime_str = start_datetime.astimezone(timezone.utc).isoformat()
        end_datetime_str = end_datetime.astimezone(timezone.utc).isoformat()

        # Create the event body
        event_body = {
            'summary': summary,
            'start': {'dateTime': start_datetime_str, 'timeZone': 'UTC'},
            'end': {'dateTime': end_datetime_str, 'timeZone': 'UTC'},
            **({'location': location} if location is not None else {}),
        }

        # Insert the event
        created_event = service.events().insert(
            calendarId='primary',
            body=event_body
        ).execute()

        return created_event

    def _run(self, summary: str, start_datetime: datetime, end_datetime: datetime, location: str):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")


class GoogleCalendarAbility(BaseAbility):
    def partial_sys_prompt(self) -> str:
        return f'''Right now is {datetime.now().astimezone().isoformat()}.
Calendar events default to 1h, my timezone is -03:00, America/Sao_Paulo.
Weeks start on sunday and end on saturday. Please consider local holidays and treat them as non-work days.'''

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        return [
            GoogleCalendarTool(),
            CreateGoogleCalendarEventTool(),
        ]
