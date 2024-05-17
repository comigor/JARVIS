import httpx
import uuid
import json
import logging
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from apscheduler.schedulers.background import BackgroundScheduler

_LOGGER = logging.getLogger(__name__)


class ScheduleActionInput(BaseModel):
    moment: datetime = Field(
        description="At which time the action should be executed (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Required."
    )
    instructions: str = Field(
        description="Complete instructions to execute the entire task as if it's time to execute it."
    )


class ScheduleActionTool(BaseTool):
    name = "schedule_action"
    description = """Use this when you want to schedule any action to be executed in the future by setting a timer and running a set of instructions.
Provide complete instructions to execute the entire task as if it's time to execute it.
For example, when the user request to "set an alarm for 4p.m.", the instructions should be "notify user their alarm has expired" 
and when the user request to "at 4p.m, send a message to John saying wake up", the instructions should be "send a message to John: wake up"."""
    args_schema: Type[BaseModel] = ScheduleActionInput

    client: httpx.Client = Field(default_factory=lambda: httpx.Client(timeout=90))
    scheduler: BackgroundScheduler = Field(default_factory=lambda: BackgroundScheduler())

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def _run(self, moment: datetime, instructions: str) -> str:
        scheduler: BackgroundScheduler = self.scheduler

        def _run_instructions():
            response = self.client.post(
                "http://192.168.10.20:10055/invoke",
                json={
                    "input": instructions,
                    "config": {"configurable": {"session_id": str(uuid.uuid4())}},
                },
            )
            json_obj = response.json()
            _LOGGER.debug(json_obj)
            return (
                json.dumps(json_obj)
                if response.status_code == 200
                else f"Sorry, I can't do that (got error {response.status_code})"
            )

        scheduler.add_job(func=_run_instructions, trigger="date", next_run_time=moment)
        return f"The action \"{instructions}\" has been scheduled to run at {moment}."
