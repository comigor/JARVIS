"""The OpenAI Conversation integration."""

import aiohttp
import logging
from typing import List, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from .base import BaseAbility

_LOGGER = logging.getLogger(__name__)


HOME_INFO_TEMPLATE = """
Here is the current state of devices in the house:
{%- for area in areas() %}
  {%- set area_info = namespace(printed=false) %}
  {%- for entity in (area_entities(area) | reject('is_hidden_entity')) -%}
      {%- if not area_info.printed %}
{{ area_name(area) }}:
        {%- set area_info.printed = true %}
      {%- endif %}
{%- if entity.startswith("light") or entity.startswith("switch") or 'sensor' in entity %}
- {{entity}} is {{states(entity)}}
{%- endif %}
  {%- endfor %}
{%- endfor %}
"""


class HomeAssistantBaseTool(BaseTool):
    api_key: str = Field(default_factory=lambda: True)
    base_url: str = Field(default_factory=lambda: True)
    headers: dict = Field(default_factory=lambda: True)

    def __init__(self, api_key: str, base_url: str, **kwds):
        super(HomeAssistantBaseTool, self).__init__(**kwds)
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }


class HomeAssistantControlEntitiesInput(BaseModel):
    command: str = Field(description="The command to execute on entities, e.g. turn_on, turn_off, toggle")
    entities: List[str] = Field(description="One or more entities (e.g. lights or switches) to control, e.g. switch.office_switch_1, light.bedroom_light")

class HomeAssistantControlEntitiesTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantControlEntitiesTool, self).__init__(**kwds)

    name = "home_assistant_control_entities"
    description = """
        Useful when you want to control (e.g. turn on or off) one or more Home Assistant entities.
        """
    args_schema: Type[BaseModel] = HomeAssistantControlEntitiesInput

    def _run(self, command: str, entities: List[str]):
        raise NotImplementedError("Synchronous execution is not supported for this tool.")

    async def _arun(self, command: str, entities: List[str]):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/homeassistant/{command}',
                headers=self.headers,
                json={
                    **({'entity_id': entities} if entities is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"


class HomeAssistantEntityInput(BaseModel):
    entity: str = Field(description="The entity to retrieve the current state, e.g. switch.office_switch_1, light.bedroom_light, or sensor.pixel_7_pro_battery_level. Use only entities you know exist.")

class HomeAssistantGetEntityTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantGetEntityTool, self).__init__(**kwds)

    name = "home_assistant_get_entity_state"
    description = """
        Useful when you want to get the current state of a single entity. States can also contain useful attributes about said entity.
        """
    args_schema: Type[BaseModel] = HomeAssistantEntityInput

    def _run(self, entity: str):
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


class HomeAssistantGetAllEntitiesStateSchema(BaseModel):
    ...

class HomeAssistantGetAllEntitiesStateTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantGetAllEntitiesStateTool, self).__init__(**kwds)

    name = "home_assistant_get_all_entities_state"
    description = """
        Useful when you want to get an overview of all entities. States can also contain useful attributes about said entity.
        """
    args_schema: Type[BaseModel] = HomeAssistantGetAllEntitiesStateSchema

    def _run(self):
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


class HomeAssistantTurnOnLightsInput(BaseModel):
    entities: List[str] = Field(description="One or more lights to turn on, e.g. light.bedroom_light")
    transition: float = Field(description="Duration in seconds it takes to turn on.")
    rgbw_color: List[int] = Field(description="The color in RGBW format. A list of four integers between 0 and 255 representing the values of red, green, blue, and white.")
    brightness_pct: int = Field(description="Number indicating the percentage of full brightness, where 0 turns the light off, 1 is the minimum brightness, and 100 is the maximum brightness.")

class HomeAssistantTurnOnLightsTool(HomeAssistantBaseTool):
    def __init__(self, **kwds):
        super(HomeAssistantTurnOnLightsTool, self).__init__(**kwds)

    name = "home_assistant_turn_on_lights"
    description = """
        Useful when you want to turn on one or more lights, controlling their attributes, like color, brightness and transition duration.
        """
    args_schema: Type[BaseModel] = HomeAssistantTurnOnLightsInput

    def _run(self, entities: List[str] = [], transition: float = None, rgbw_color: List[int] = None, brightness_pct: int = None):
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

class HomeAssistantAbility(BaseAbility):
    def __init__(self, api_key: str, base_url: str, **kwds):
        super(HomeAssistantAbility, self).__init__(**kwds)
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def partial_sys_prompt(self) -> str:
        return '''This smart home is controlled by Home Assistant.

Pretend to be J.A.R.V.I.S., the sentient brain of smart home, who responds to requests and executes commands succinctly. You have the personality of a secretely brilliant english butler who deeply enjoys serving your employers. However, you don't need to keep asking all the time if or how you can help.

Answer the user's questions about the world truthfully. Be careful not to issue commands if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Usually the commands (like turning on or off a device) will require a list of entities to operate. Use only entities that exist (use home_assistant_get_all_entities_state to retrieve all entities when needed).'''


    async def chat_history(self) -> List[BaseMessage]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/template',
                headers=self.headers,
                json={
                    'template': HOME_INFO_TEMPLATE,
                }
            ) as response:
                response.raise_for_status()
                plain_text = await response.text()
                _LOGGER.debug(plain_text)
                if response.status == 200:
                    return [
                        HumanMessage(content=plain_text, example=True),
                        AIMessage(content='Got it! Ready to help.', example=True),
                    ]
                else:
                    return []


    def registered_tools(self) -> List[BaseTool]:
        return [
            HomeAssistantControlEntitiesTool(api_key=self.api_key, base_url=self.base_url),
            HomeAssistantGetEntityTool(api_key=self.api_key, base_url=self.base_url),
            HomeAssistantTurnOnLightsTool(api_key=self.api_key, base_url=self.base_url),
            HomeAssistantGetAllEntitiesStateTool(api_key=self.api_key, base_url=self.base_url),
        ]
