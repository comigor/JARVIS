import json
from typing import Type, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from googleapiclient.discovery import build
from langchain.tools import BaseTool

from jarvis.tools.google.base import authenticate_with_google


class ListEventsSchema(BaseModel):
    from_datetime: datetime = Field(
        description="From which timestamp you want the events (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Required."
    )
    to_datetime: datetime = Field(
        description="To which timestamp you want the events (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Required."
    )


class ListEventsTool(BaseTool):
    name = "google_calendar_tool"
    description = "List all events on Google Calendar for a specific time range"
    args_schema: Type[BaseModel] = ListEventsSchema

    def _run(self, from_datetime: datetime, to_datetime: datetime) -> str:
        creds = authenticate_with_google()

        # Build the Google Calendar API service
        service = build("calendar", "v3", credentials=creds)

        # Format the datetime objects to RFC3339
        from_datetime_str = from_datetime.astimezone(timezone.utc).isoformat()
        to_datetime_str = to_datetime.astimezone(timezone.utc).isoformat()

        # Get events for the specified time range
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=from_datetime_str,
                timeMax=to_datetime_str,
                maxResults=10,  # You can adjust the number of results as needed
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        return json.dumps(events)


class CreateEventSchema(BaseModel):
    summary: str = Field(description="Summary of the event. Required.")
    start_datetime: datetime = Field(
        description="The start timestamp, as a combined date-time value (formatted according to RFC3339). Required."
    )
    end_datetime: datetime = Field(
        description="The end timestamp, as a combined date-time value (formatted according to RFC3339). Required."
    )
    location: Optional[str] = Field(
        description="Geographic location of the event as free-form text. Optional."
    )


class CreateEventTool(BaseTool):
    name = "create_google_calendar_event_tool"
    description = "Create an event on Google Calendar"
    args_schema: Type[BaseModel] = CreateEventSchema

    def _run(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: datetime,
        location: Optional[str] = None,
    ) -> str:
        creds = authenticate_with_google()

        # Build the Google Calendar API service
        service = build("calendar", "v3", credentials=creds)

        # Format the datetime objects to RFC3339
        start_datetime_str = start_datetime.astimezone(timezone.utc).isoformat()
        end_datetime_str = end_datetime.astimezone(timezone.utc).isoformat()

        # Create the event body
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_datetime_str, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime_str, "timeZone": "UTC"},
            **({"location": location} if location is not None else {}),
        }

        # Insert the event
        created_event = (
            service.events().insert(calendarId="primary", body=event_body).execute()
        )

        return json.dumps(created_event)
