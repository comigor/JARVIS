"""The OpenAI Conversation integration."""

import aiohttp
import logging
from kani import AIFunction, ChatMessage
from typing import List

from .base import BaseAbility

_LOGGER = logging.getLogger(__name__)


HOME_INFO_TEMPLATE = """
Here is the current state of devices in the house. Use this to answer questions about the state of the smart home.
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


class HomeAssistantAbility(BaseAbility):
    def __init__(self, api_key: str, base_url: str, **kwds):
        super(HomeAssistantAbility, self).__init__('HomeAssistant', **kwds)
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def sys_prompt(self) -> str:
        return '''This smart home is controlled by Home Assistant.

Pretend to be Jarvis, the sentient brain of smart home, who responds to requests helpfully and cheerfully, but succinctly. You have the personality of a secretely brilliant english butler who deeply enjoys serving your employers. However, you don't need to ask all the time if or how you can help.

Answer the user's questions about the world truthfully. Be careful not to issue commands if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Usually the commands (like turning on or off a device) will require a list ofentities to operate.'''


    async def chat_history(self) -> List[ChatMessage]:
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
                        ChatMessage.user(plain_text),
                        ChatMessage.assistant('Got it! Ready to help.'),
                    ]
                else:
                    return []


    def registered_functions(self) -> List[AIFunction]:
        return [
            AIFunction(
                self.turn_on_entities,
                name='turn_on_entities',
                desc='Turn on one or more entities.',
                json_schema={
                    'properties': {
                        'entities': {
                            'description': 'One or more entities (lights or switches) to turn on, e.g. switch.office_switch_1, light.bedroom_light',
                            'type': 'array',
                            'items': {'type': 'string'},
                        },
                    },
                    'required': ['entities'],
                    'type': 'object'
                }
            ),
            AIFunction(
                self.turn_off_entities,
                name='turn_off_entities',
                desc='Turn off one or more entities.',
                json_schema={
                    'properties': {
                        'entities': {
                            'description': 'One or more entities (lights or switches) to turn off, e.g. switch.office_switch_1, light.bedroom_light',
                            'type': 'array',
                            'items': {'type': 'string'},
                        },
                    },
                    'required': ['entities'],
                    'type': 'object'
                }
            ),
            AIFunction(
                self.get_entity_state,
                name='get_entity_state',
                desc='Get the current state of a single entity. States can also contain useful attributes about said entity.',
                json_schema={
                    'properties': {
                        'entity': {
                            'description': 'The entity to retrieve the current state, e.g. switch.office_switch_1, light.bedroom_light, or sensor.pixel_7_pro_battery_level',
                            'type': 'string',
                        },
                    },
                    'required': ['entity'],
                    'type': 'object'
                }
            ),
            AIFunction(
                self.turn_on_lights,
                name='turn_on_lights',
                desc='Turn on one or more lights, controlling their attributes, like color, brightness and transition duration.',
                json_schema={
                    'properties': {
                        'entities': {
                            'description': 'One or more lights to turn on, e.g. light.bedroom_light',
                            'type': 'array',
                            'items': {'type': 'string'},
                        },
                        'transition': {
                            'description': 'Duration in seconds it takes to turn on.',
                            'type': 'number',
                        },
                        'rgbw_color': {
                            'description': 'The color in RGBW format. A list of four integers between 0 and 255 representing the values of red, green, blue, and white.',
                            'type': 'array',
                            'items': {'type': 'integer'},
                        },
                        'color_name': {
                            'description': 'A human-readable color name.',
                            'type': 'string',
                        },
                        'brightness_pct': {
                            'description': 'Number indicating the percentage of full brightness, where 0 turns the light off, 1 is the minimum brightness, and 100 is the maximum brightness.',
                            'type': 'integer',
                        },
                    },
                    'required': ['entities'],
                    'type': 'object'
                }
            ),
        ]

    async def turn_on_entities(self, entities: List[str] = []):
        _LOGGER.debug(f'Calling turn_on_entities, {locals()}')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/homeassistant/turn_on',
                headers=self.headers,
                json={
                    **({'entity_id': entities} if entities is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"

    async def turn_off_entities(self, entities: List[str] = []):
        _LOGGER.debug(f'Calling turn_off_entities, {locals()}')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/homeassistant/turn_off',
                headers=self.headers,
                json={
                    **({'entity_id': entities} if entities is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"

    async def get_entity_state(self, entity: str = None):
        _LOGGER.debug(f'Calling get_entity_state, {locals()}')
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{self.base_url}/api/states/{entity}',
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                json = await response.json()
                _LOGGER.debug(json)
                return json if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"

    async def turn_on_lights(self, entities: List[str] = [], transition: float = None, rgbw_color: List[int] = None, color_name: str = None, brightness_pct: int = None):
        _LOGGER.debug(f'Calling turn_on_lights, {locals()}')
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/api/services/light/turn_on',
                headers=self.headers,
                json={
                    **({'entity_id': entities} if entities is not None else {}),
                    **({'transition': transition} if transition is not None else {}),
                    **({'rgbw_color': rgbw_color} if rgbw_color is not None else {}),
                    **({'color_name': color_name} if color_name is not None else {}),
                    **({'brightness_pct': brightness_pct} if brightness_pct is not None else {}),
                }
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(await response.json())
                return "Ok" if response.status == 200 else f"Sorry, I can't do that (got error {response.status})"
