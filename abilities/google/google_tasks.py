from typing import Type, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from googleapiclient.discovery import build
from langchain.tools import BaseTool
from langchain_core.messages import BaseMessage

from .base import authenticate_with_google
from ..base import BaseAbility
from ..fuckio import async_add_executor_job

class ListGoogleTasksSchema(BaseModel):
    from_datetime: datetime = Field(
        None,
        description='From which timestamp you want to list tasks (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z)'
    )
    to_datetime: datetime = Field(
        None,
        description='To which timestamp you want to list tasks (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T11:00:00-07:00, 2011-06-03T11:00:00Z)'
    )
    show_completed: bool = Field(
        False,
        description='Whether to show completed tasks'
    )
    show_deleted: bool = Field(
        False,
        description='Whether to show deleted tasks'
    )
    show_hidden: bool = Field(
        False,
        description='Whether to show hidden tasks'
    )

class CreateGoogleTaskSchema(BaseModel):
    title: str = Field(description='Title of the task')
    due_datetime: datetime = Field(None, description='Due timestamp of the task (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z)')

class GoogleTasksTool(BaseTool):
    name = 'google_tasks_tool'
    description = 'List tasks using Google Tasks API'
    args_schema: Type[BaseModel] = ListGoogleTasksSchema

    async def _arun(
        self,
        from_datetime: datetime = None,
        to_datetime: datetime = None,
        show_completed: bool = False,
        show_deleted: bool = False,
        show_hidden: bool = False
    ):
        creds = await authenticate_with_google()

        # Build the Google Tasks API service
        service = await async_add_executor_job(build, 'tasks', 'v1', credentials=creds)

        # Format the datetime objects to RFC3339
        from_datetime_str = from_datetime.astimezone(timezone.utc).isoformat() if from_datetime else None
        to_datetime_str = to_datetime.astimezone(timezone.utc).isoformat() if to_datetime else None

        # List tasks for the specified time range
        tasks_result = service.tasks().list(
            tasklist='@default',  # Use the default task list
            dueMin=from_datetime_str,
            dueMax=to_datetime_str,
            showCompleted=show_completed,
            showDeleted=show_deleted,
            showHidden=show_hidden,
        ).execute()

        tasks = tasks_result.get('items', [])

        return tasks

    def _run(
        self,
        from_datetime: datetime = None,
        to_datetime: datetime = None,
        show_completed: bool = False,
        show_deleted: bool = False,
        show_hidden: bool = False
    ):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

class CreateGoogleTaskTool(BaseTool):
    name = 'create_google_task_tool'
    description = 'Create a task using Google Tasks API'
    args_schema: Type[BaseModel] = CreateGoogleTaskSchema

    async def _arun(self, title: str, due_datetime: datetime):
        creds = await authenticate_with_google()

        # Build the Google Tasks API service
        service = await async_add_executor_job(build, 'tasks', 'v1', credentials=creds)

        # Format the datetime object to RFC3339
        due_datetime_str = due_datetime.astimezone(timezone.utc).isoformat() if due_datetime else None

        # Create the task body
        task_body = {
            'title': title,
            **({'due': due_datetime_str} if due_datetime_str is not None else {}),
        }

        # Insert the task
        created_task = service.tasks().insert(
            tasklist='@default',  # Use the default task list
            body=task_body
        ).execute()

        return created_task

    def _run(self, title: str, due_datetime: datetime):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")


class GoogleTasksAbility(BaseAbility):
    def partial_sys_prompt(self) -> str:
        return "Help user list, create and be reminded of their things to do. They can use the words TODO, to-do, task, tarefa, lembrete, along others for this."

    async def chat_history(self) -> List[BaseMessage]:
        return []

    def registered_tools(self) -> List[BaseTool]:
        return [GoogleTasksTool(), CreateGoogleTaskTool()]
