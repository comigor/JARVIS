import aiohttp
import logging
from typing import Any, Type
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantEntityInput(BaseModel):
    entity: str = Field(description="The entity ID to retrieve the current state, e.g. switch.office_switch_1, light.bedroom_light, or sensor.pixel_7_pro_battery_level. Use only entities you know exist.")

class HomeAssistantGetEntityTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantGetEntityTool, self).__init__(**kwds)

    name = "home_assistant_get_entity_state"
    description = "Get the current state of a single entity. States can also contain useful attributes about said entity."
    args_schema: Type[BaseModel] = HomeAssistantEntityInput

    def _run(self, **kwargs: Any):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, entity: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.base_url}/api/states/{entity}',
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                json = await response.json()
                _LOGGER.debug(json)
                return json if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"
