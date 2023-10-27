"""The OpenAI Conversation integration."""
# For relative imports to work in Python 3.6
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import logging
import traceback

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.util import ulid
from typing import Literal
from kani import Kani

from . import brains
from .abilities.homeassistant import HomeAssistantAbility
from .abilities.google import GoogleAbility

from .const import (
    CONF_OPENAI_KEY_KEY,
    CONF_HA_KEY_KEY,
    CONF_HA_URL_KEY,
    DOMAIN,
    CONF_GOOGLE_API_KEY,
    CONF_GOOGLE_CX_KEY,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Conversation from a config entry."""
    _LOGGER.debug(entry)
    _LOGGER.debug(entry.data)
    _LOGGER.debug(entry.data.items())
    _LOGGER.debug(entry.data.keys())
    _LOGGER.debug(entry.options)
    openai_key = entry.data.get(CONF_OPENAI_KEY_KEY)
    homeassistant_key = entry.data.get(CONF_HA_KEY_KEY)
    homeassistant_url = entry.data.get(CONF_HA_URL_KEY)
    google_api_key = entry.data.get(CONF_GOOGLE_API_KEY)
    google_cx_key = entry.data.get(CONF_GOOGLE_CX_KEY)

    try:
        abilities = []

        abilities.extend([HomeAssistantAbility(api_key=homeassistant_key, base_url=homeassistant_url)]
                         if (homeassistant_key and homeassistant_url) else [])
        abilities.extend([GoogleAbility(api_key=google_api_key, cx_key=google_cx_key)]
                         if (google_api_key and google_cx_key) else [])

        ai = await brains.get_ai(openai_key=openai_key, abilities=abilities)

    except Exception as err:
        _LOGGER.error(f"Sorry, I had a problem: {err}\n{traceback.format_exc()}")
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data[CONF_OPENAI_KEY_KEY]

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

        last_msg_text = None
        try:
            _LOGGER.info('FULL ROUND:')
            async for msg in self.ai.full_round(user_input.text):
                _LOGGER.info(f'msg: {msg}')
                last_msg_text = msg.text
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
        intent_response.async_set_speech(last_msg_text)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )
