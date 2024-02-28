import aiohttp
import logging
from typing import Any, Type
from pydantic import BaseModel

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantListEntitiesStateSchema(BaseModel):
    ...

class HomeAssistantListEntitiesStateTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantListEntitiesStateTool, self).__init__(**kwds)

    name = "home_assistant_get_all_entities_state"
    description = "Get an overview of all entities, including their IDs and state. States can also contain useful attributes about said entity."
    args_schema: Type[BaseModel] = HomeAssistantListEntitiesStateSchema

    def _run(self, **kwargs: Any):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.base_url}/api/states',
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                json = list(filter(lambda s: s.get('entity_id').startswith(('light', 'switch', 'sensor')), await response.json()))
                _LOGGER.debug(json)
                return json if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"
