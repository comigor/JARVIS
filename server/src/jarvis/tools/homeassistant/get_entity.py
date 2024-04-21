import logging
import json
from typing import Type
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantEntityInput(BaseModel):
    entity: str = Field(
        description="The entity ID to retrieve the current state, e.g. switch.office_switch_1, light.bedroom_light, or sensor.pixel_7_pro_battery_level. Use only entities you know exist."
    )


class HomeAssistantGetEntityTool(HomeAssistantBaseTool):
    name = "home_assistant_get_entity_state"
    description = "Get the current state of a single entity. States can also contain useful attributes about said entity."
    args_schema: Type[BaseModel] = HomeAssistantEntityInput

    def _run(self, entity: str) -> str:
        response = self.client.get(
            f"{self.base_url}/api/states/{entity}",
            headers=self.headers,
        )
        response.raise_for_status()
        json_obj = response.json()
        _LOGGER.debug(json_obj)
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status})"
        )
