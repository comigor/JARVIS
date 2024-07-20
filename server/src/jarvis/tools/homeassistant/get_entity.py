import logging
import json
import traceback
from typing import Type
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantEntityInput(BaseModel):
    entity: str = Field(
        description="The entity ID to retrieve the current state, e.g. switch.office_switch_1, light.bedroom_light, or sensor.pixel_7_pro_battery_level. Use only entities you know exist, in doubt, run home_assistant_get_all_entities_state first."
    )


class HomeAssistantGetEntityTool(HomeAssistantBaseTool):
    name = "home_assistant_get_entity_state"
    description = "Get the current state of a single entity. States can also contain useful attributes about said entity."
    args_schema: Type[BaseModel] = HomeAssistantEntityInput

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self, entity: str) -> str:
        try:
            _LOGGER.debug("igor0")
            response = self.client.get(
                f"{self.base_url}/api/states/{entity}",
                headers=self.headers,
            )
            _LOGGER.debug("igor1")
            json_obj = response.json()
            _LOGGER.debug(json_obj)
            _LOGGER.debug("igor2")
        except Exception as err:
            _LOGGER.debug(response)
            _LOGGER.debug(err)
            _LOGGER.error(f"Sorry, there was an error: {err}\n{traceback.format_exc()}")
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
