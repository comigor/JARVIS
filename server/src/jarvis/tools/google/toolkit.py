import os
from typing import List

from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_community.tools import BaseTool

from langchain_google_community import GoogleSearchRun, GoogleSearchAPIWrapper

from jarvis.tools.google import calendar
from jarvis.tools.google import tasks


class GoogleToolkit(BaseToolkit):
    class Config:
        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        return [
            GoogleSearchRun(
                api_wrapper=GoogleSearchAPIWrapper(
                    google_api_key=os.environ["GOOGLE_API_KEY"],
                    google_cse_id=os.environ["GOOGLE_CSE_ID"],
                ),
            ),
            calendar.ListEventsTool(),
            calendar.CreateEventTool(),
            tasks.ListTasksTool(),
            tasks.CreateTaskTool(),
        ]
