import logging
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field
from apscheduler.schedulers.background import BackgroundScheduler

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool
from jarvis.tools.homeassistant.notify_alexa import HomeAssistantNotifyAlexaTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantTimerInput(BaseModel):
    message: str = Field(
        description="The timer description"
    )
    moment: datetime = Field(
        description="At which time the timer should trigger (RFC3339 timestamp with mandatory time zone offset, e.g., 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z). Required."
    )


class HomeAssistantTimerTool(HomeAssistantBaseTool):
    name = "home_assistant_timer"
    description = "Useful when you want to set an alarm at some time."
    args_schema: Type[BaseModel] = HomeAssistantTimerInput

    scheduler: BackgroundScheduler = Field(default_factory=lambda: BackgroundScheduler())
    notify_alexa: HomeAssistantNotifyAlexaTool = Field(default_factory=lambda: None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.notify_alexa = HomeAssistantNotifyAlexaTool(**kwds)
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def _run(self, message: str, moment: datetime) -> str:
        scheduler: BackgroundScheduler = self.scheduler
        scheduler.add_job(func=self.notify_alexa._run, args=[message, "media_player.igor_s_echo_dot"], trigger="date", next_run_time=moment)
        return "Done."
