"""The OpenAI Conversation integration."""

import os
import logging
import asyncio
from typing import Callable
from kani import Kani, chat_in_terminal_async
from kani.engines.openai import OpenAIEngine
from functools import partial

from abilities.homeassistant import HomeAssistantAbility
from abilities.base import BaseAbility

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def get_ai(openai_key: str, abilities: [BaseAbility] = [], wrapper: Callable = lambda x: x):
    _LOGGER.debug('Starting up OpenAIEngine')
    engine = OpenAIEngine(openai_key, model="gpt-3.5-turbo-0613", max_context_size=4096)

    system_prompt = ''
    chat_history = []
    all_functions = []

    _LOGGER.debug(f'Registering abilities')
    for ability in abilities:
        _LOGGER.debug(f'\nRegistering ability: {ability.name}')
        prompt = ability.sys_prompt()
        history = ability.chat_history()
        functions = ability.registered_functions()

        _LOGGER.debug(f'System prompt: {prompt}')
        _LOGGER.debug(f'Chat history: {history}')
        _LOGGER.debug(f'Functions: {functions}')

        system_prompt += prompt
        chat_history += history
        all_functions += functions

    # for fun in all_functions:
    #     fun.inner = partial(wrapper, fun.inner)

    return Kani(
        engine=engine,
        system_prompt=system_prompt,
        chat_history=chat_history,
        functions=all_functions,
    )

# ------------------------------------------
# To mock HomeAssistant

class MyHass:
    def __init__(self):
        self.loop = asyncio.get_running_loop()

    def async_add_executor_job(
        self, target: Callable, *args
    ) -> asyncio.Future:
        """Add an executor job from within the event loop."""
        task = self.loop.run_in_executor(None, target, *args)
        return task

def wrap_into_ha(hass):
    async def wrapper(fun: Callable, *args, **kwargs):
        compacted = partial(fun, *args, **kwargs)
        _LOGGER.error('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        _LOGGER.error(fun)
        _LOGGER.error(args)
        _LOGGER.error(kwargs)
        await compacted()
        # await hass.async_add_executor_job(compacted)
    return wrapper

# ------------------------------------------

async def main():
    # ability = HomeAssistantAbility(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url='https://homeassistant.brick.borges.me:2443')
    # await ability.turn_off('light.office_light')
    # wrapped = wrap_into_ha(MyHass())
    # await wrapped(ability.turn_on, entity='light.office_light')

    abilities = [
        HomeAssistantAbility(api_key=os.getenv('HOMEASSISTANT_KEY'), base_url='https://homeassistant.brick.borges.me:2443'),
    ]
    openai_key = os.getenv('OPENAI_KEY')
    ai = await get_ai(openai_key=openai_key, abilities=abilities, wrapper=wrap_into_ha(MyHass()))

    await chat_in_terminal_async(ai)


if __name__ == '__main__':
    asyncio.run(main())
