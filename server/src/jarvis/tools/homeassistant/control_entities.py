import logging
import json
from typing import List, Type
from pydantic import BaseModel, Field
from enum import Enum

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class CommandEnum(str, Enum):
    turn_on = "turn_on"
    turn_off = "turn_off"
    toggle = "toggle"


class HomeAssistantControlEntitiesInput(BaseModel):
    command: CommandEnum = Field(
        description="The command to execute on entities, e.g. turn_on, turn_off, toggle"
    )
    entities: List[str] = Field(
        description="The entity IDs of devices (e.g. lights or switches) to control, e.g. switch.office_switch_1, light.bedroom_light"
    )


class HomeAssistantControlEntitiesTool(HomeAssistantBaseTool):
    name: str = "home_assistant_control_entities"
    description: str = "Useful when you want to control (e.g. turn on or off) one or more Home Assistant entities."
    args_schema: Type[BaseModel] = HomeAssistantControlEntitiesInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, command: CommandEnum, entities: List[str]) -> str:
        response = self.client.post(
            f"{self.base_url}/api/services/homeassistant/{command.value}",
            headers=self.headers,
            json={
                **({"entity_id": entities} if entities is not None else {}),
            },
        )
        json_obj = response.json()
        _LOGGER.debug(json_obj)
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
