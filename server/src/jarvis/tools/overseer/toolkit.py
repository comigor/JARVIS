from typing import List
from pydantic import Field

from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_core.tools import BaseTool

from jarvis.tools.overseer.request import OverseerDownloadTool
from jarvis.tools.overseer.search import OverseerSearchTool


class OverseerToolkit(BaseToolkit):
    api_key: str = Field(default_factory=lambda: "")
    base_url: str = Field(default_factory=lambda: "")

    class Config:
        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        return [
            OverseerSearchTool(base_url=self.base_url, api_key=self.api_key),
            OverseerDownloadTool(base_url=self.base_url, api_key=self.api_key),
        ]
