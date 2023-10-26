"""The OpenAI Conversation integration."""

import aiohttp
import logging
from kani import AIFunction, ChatMessage

from .base import BaseAbility

_LOGGER = logging.getLogger(__name__)


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

Pretend to be Jarvis, the sentient brain of smart home, who responds to requests helpfully and cheerfully, but succinctly. You have the personality of a secretely brilliant english butler who deeply enjoys serving your employers.

Answer the user's questions about the world truthfully. Be careful not to issue commands if the user is only seeking information. i.e. if the user says "are the lights on in the kitchen?" just provide an answer.

Usually the commands (like turning on or off a device) will require a list ofentities to operate.'''


    def chat_history(self) -> [ChatMessage]:
        return [
            ChatMessage.user('''Here is the current state of devices in the house, by area they are present. Use this to answer questions about the state of the smart home.
Living Room:
  - light.living_room_light_2 is off
  - light.living_room_light_1 is off
  - light.living_room is off
Bedroom:
  - light.bedroom_light is off
  - light.bedroom is off
Office:
  - light.office_light is off
  - light.office is off
  - switch.office_switch_1 is off
  - switch.office_switch_2 is off
'''),
            ChatMessage.assistant('Got it! Ready to help.'),
        ]


    def registered_functions(self) -> [AIFunction]:
        return [
            AIFunction(
                self.turn_on,
                name='turn_on',
                desc='Turn on one or more entities.',
                json_schema={
                    'properties': {
                        'entities': {
                            'description': 'One or more entities to turn on, e.g. switch.office_switch_1, light.bedroom_light',
                            'type': 'array',
                            'items': {'type': 'string'},
                        },
                    },
                    'required': ['entities'],
                    'type': 'object'
                }
            ),
            AIFunction(
                self.turn_off,
                name='turn_off',
                desc='Turn off one or more entities.',
                json_schema={
                    'properties': {
                        'entities': {
                            'description': 'One or more entities to turn off, e.g. switch.office_switch_1, light.bedroom_light',
                            'type': 'array',
                            'items': {'type': 'string'},
                        },
                    },
                    'required': ['entities'],
                    'type': 'object'
                }
            ),
        ]

    async def turn_on(self, entities: str = None):
        _LOGGER.debug(f'Calling turn_on, {locals()}')
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


    async def turn_off(self, entities: str = None):
        _LOGGER.debug(f'Calling turn_off, {locals()}')
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
