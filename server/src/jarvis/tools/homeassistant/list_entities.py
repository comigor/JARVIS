import json
import logging
from typing import Type
from pydantic import BaseModel

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantListEntitiesStateSchema(BaseModel): ...


class HomeAssistantListAllEntitiesTool(HomeAssistantBaseTool):
    name = "home_assistant_list_all_entities"
    description = "Get an overview of all entities, including their IDs and state. States can also contain useful attributes about said entity."
    args_schema: Type[BaseModel] = HomeAssistantListEntitiesStateSchema

    def __init__(self, **kwds):
        super().__init__(**kwds)

    def _run(self) -> str:
        response = self.client.get(
            f"{self.base_url}/api/states",
            headers=self.headers,
        )
        json_obj = list(
            map(
                lambda s: {
                    "entity_id": s.get("entity_id"),
                    "entity_type": s.get("entity_id").split(".")[0],
                    "state": s.get("state"),
                },
                filter(
                    lambda s: s.get("entity_id").startswith(
                        ("light", "switch", "sensor")
                    ),
                    response.json(),
                ),
            )
        )
        _LOGGER.debug(json_obj)
        return (
            json.dumps(json_obj)
            if response.status_code == 200
            else f"Sorry, I can't do that (got error {response.status_code})"
        )
