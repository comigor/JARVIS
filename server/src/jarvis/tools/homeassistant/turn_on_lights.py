import aiohttp
import logging
from typing import List, Any, Type, Optional
from pydantic import BaseModel, Field

from jarvis.tools.homeassistant.base import HomeAssistantBaseTool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantTurnOnLightsInput(BaseModel):
    entities: List[str] = Field(description="One or more lights to turn on, e.g. light.bedroom_light")
    transition: Optional[float] = Field(description="Duration in seconds it takes to turn on.")
    rgbw_color: Optional[List[int]] = Field(description="The color in RGBW format. A list of four integers between 0 and 255 representing the values of red, green, blue, and white.")
    brightness_pct: Optional[int] = Field(description="Number indicating the percentage of full brightness, where 0 turns the light off, 1 is the minimum brightness, and 100 is the maximum brightness.")

class HomeAssistantTurnOnLightsTool(HomeAssistantBaseTool):
    name = "home_assistant_turn_on_lights"
    description = "Turn on one or more lights, controlling their attributes, like color, brightness and transition duration."
    args_schema: Type[BaseModel] = HomeAssistantTurnOnLightsInput

    def _run(self, **kwargs: Any):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, entities: List[str] = [], transition: float = None, rgbw_color: List[int] = None, brightness_pct: int = None):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/light/turn_on',
                headers=self.headers,
                json={
                    **({'entity_id': entities} if entities is not None else {}),
                    **({'transition': transition} if transition is not None else {}),
                    **({'rgbw_color': rgbw_color} if rgbw_color is not None else {}),
                    **({'brightness_pct': brightness_pct} if brightness_pct is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"
