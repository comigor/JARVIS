from typing import List
from pydantic import Field

from langchain_community.agent_toolkits.base import BaseToolkit
from langchain_core.tools import BaseTool

from jarvis.tools.homeassistant.turn_on_lights import HomeAssistantTurnOnLightsTool
from jarvis.tools.homeassistant.control_entities import HomeAssistantControlEntitiesTool
from jarvis.tools.homeassistant.get_entity import HomeAssistantGetEntityTool
from jarvis.tools.homeassistant.list_entities import HomeAssistantListAllEntitiesTool
from jarvis.tools.homeassistant.notify_alexa import HomeAssistantNotifyAlexaTool
from jarvis.tools.homeassistant.timer import HomeAssistantTimerTool


class HomeAssistantToolkit(BaseToolkit):
    api_key: str = Field(default_factory=lambda: "")
    base_url: str = Field(default_factory=lambda: "")

    class Config:
        arbitrary_types_allowed = True

    def get_tools(self) -> List[BaseTool]:
        return [
            HomeAssistantTurnOnLightsTool(base_url=self.base_url, api_key=self.api_key),
            HomeAssistantControlEntitiesTool(
                base_url=self.base_url, api_key=self.api_key
            ),
            HomeAssistantGetEntityTool(base_url=self.base_url, api_key=self.api_key),
            HomeAssistantListAllEntitiesTool(
                base_url=self.base_url, api_key=self.api_key
            ),
            HomeAssistantNotifyAlexaTool(base_url=self.base_url, api_key=self.api_key),
            HomeAssistantTimerTool(base_url=self.base_url, api_key=self.api_key),
        ]
