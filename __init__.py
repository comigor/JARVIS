"""The OpenAI Conversation integration."""
from __future__ import annotations

import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.util import ulid
import traceback

from typing import Literal
from kani import Kani

import brains
from abilities.homeassistant import HomeAssistantAbility

from .const import (
    CONF_OPENAI_KEY,
    CONF_HA_KEY,
    CONF_HA_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Conversation from a config entry."""
    openai_key = entry.data[CONF_OPENAI_KEY]
    homeassistant_key = entry.data[CONF_HA_KEY]
    homeassistant_url = entry.data[CONF_HA_URL]

    try:
        # await hass.async_add_executor_job(
        #     partial(
        #         openai.Engine.list,
        #         api_key=entry.data[CONF_API_KEY],
        #         request_timeout=10,
        #     )
        # )
        abilities = [
            HomeAssistantAbility(api_key=homeassistant_key, base_url=homeassistant_url),
        ]
        ai = await brains.get_ai(openai_key=openai_key, abilities=abilities)

    except Exception as err:
        _LOGGER.error(f"Sorry, I had a problem with my template: {err}\n{traceback.format_exc()}")
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data[CONF_API_KEY]

    conversation.async_set_agent(hass, entry, OpenAIAgent(hass, ai, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, ai: Kani, entry: ConfigEntry) -> bool:
    """Unload OpenAI."""
    hass.data[DOMAIN].pop(entry.entry_id)
    conversation.async_unset_agent(hass, entry)
    return True


class OpenAIAgent(conversation.AbstractConversationAgent):
    """OpenAI conversation agent."""

    def __init__(self, hass: HomeAssistant, ai: Kani, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.ai = ai
        self.entry = entry

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        conversation_id = user_input.conversation_id or ulid.ulid()

        _LOGGER.info('STARTING CONVERSATION')
        _LOGGER.info(conversation_id)

        last_msg = None
        try:
            _LOGGER.info('FULL ROUND:')
            async for msg in self.ai.full_round(user_input.text):
                _LOGGER.info(msg)
                _LOGGER.info(msg.function_call)
                _LOGGER.info(msg.text)
                last_msg = msg.text
        except Exception as err:
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, there was an error: {err}\n{traceback.format_exc()}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(last_msg)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )
