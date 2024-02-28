import aiohttp
import logging
from typing import List, Any, Type, Optional
from pydantic import BaseModel, Field
from enum import Enum

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class CommandEnum(str, Enum):
    turn_on = 'turn_on'
    turn_off = 'turn_off'
    toggle = 'toggle'

class HomeAssistantControlEntitiesInput(BaseModel):
    command: CommandEnum = Field(description="The command to execute on entities, e.g. turn_on, turn_off, toggle")
    entities: Optional[List[str]] = Field(description="The entity IDs of devices (e.g. lights or switches) to control, e.g. switch.office_switch_1, light.bedroom_light")

class HomeAssistantControlEntitiesTool(HomeAssistantBaseTool):
    name = "home_assistant_control_entities"
    description = "Useful when you want to control (e.g. turn on or off) one or more Home Assistant entities."

    args_schema: Type[BaseModel] = HomeAssistantControlEntitiesInput

    def _run(self, **kwargs: Any):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, command: CommandEnum, entities: List[str]):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/homeassistant/{command.value}',
                headers=self.headers,
                json = {
                    **({'entity_id': entities} if entities is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"
