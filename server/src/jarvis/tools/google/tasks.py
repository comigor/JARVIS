import json
from typing import Type, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from googleapiclient.discovery import build
from langchain.tools import BaseTool

from jarvis.tools.google.base import authenticate_with_google


class ListGoogleTasksSchema(BaseModel):
    from_datetime: Optional[datetime] = Field(
        None,
        description="From which timestamp you want to list tasks (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Optional.",
    )
    to_datetime: Optional[datetime] = Field(
        None,
        description="To which timestamp you want to list tasks (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T11:00:00-07:00, 2011-06-03T11:00:00Z). Optional.",
    )
    show_completed: Optional[bool] = Field(
        False, description="Whether to show completed tasks. Optional."
    )
    show_deleted: Optional[bool] = Field(
        False, description="Whether to show deleted tasks. Optional."
    )
    show_hidden: Optional[bool] = Field(
        False, description="Whether to show hidden tasks. Optional."
    )


class ListTasksTool(BaseTool):
    name = "google_list_tasks_tool"
    description = "List tasks using Google Tasks API"
    args_schema: Type[BaseModel] = ListGoogleTasksSchema

    def _run(
        self,
        from_datetime: Optional[datetime] = None,
        to_datetime: Optional[datetime] = None,
        show_completed: Optional[bool] = False,
        show_deleted: Optional[bool] = False,
        show_hidden: Optional[bool] = False,
    ) -> str:
        creds = authenticate_with_google()

        # Build the Google Tasks API service
        service = build("tasks", "v1", credentials=creds)

        # Get default tasklist ID
        default_tasklist_id = service.tasklists().list().execute()["items"][0]["id"]
        default_tasklist_id = "@default"

        # Format the datetime objects to RFC3339
        from_datetime_str = (
            from_datetime.astimezone(timezone.utc).isoformat()
            if from_datetime
            else None
        )
        to_datetime_str = (
            to_datetime.astimezone(timezone.utc).isoformat() if to_datetime else None
        )

        # List tasks for the specified time range
        tasks_result = (
            service.tasks()
            .list(
                tasklist=default_tasklist_id,
                dueMin=from_datetime_str,
                dueMax=to_datetime_str,
                showCompleted=show_completed,
                showDeleted=show_deleted,
                showHidden=show_hidden,
            )
            .execute()
        )

        tasks = tasks_result.get("items", [])

        return json.dumps(tasks)


class CreateTaskSchema(BaseModel):
    task_title: str = Field(description="Title of the task. Required.")
    due_datetime: datetime = Field(
        description="Due timestamp of the task (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Required."
    )


class CreateTaskTool(BaseTool):
    name = "google_create_task_tool"
    description = "Create a task using Google Tasks API"
    args_schema: Type[BaseModel] = CreateTaskSchema

    def _run(self, task_title: str, due_datetime: datetime) -> str:
        creds = authenticate_with_google()

        # Build the Google Tasks API service
        service = build("tasks", "v1", credentials=creds)

        # Get default tasklist ID
        default_tasklist_id = service.tasklists().list().execute()["items"][0]["id"]
        default_tasklist_id = "@default"

        # Format the datetime object to RFC3339
        due_datetime_str = due_datetime.astimezone(timezone.utc).isoformat()

        # Create the task body
        task_body = {
            "title": task_title,
            "due": due_datetime_str,
        }

        # Insert the task
        created_task = (
            service.tasks()
            .insert(tasklist=default_tasklist_id, body=task_body)
            .execute()
        )

        return json.dumps(created_task)
