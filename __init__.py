"""The OpenAI Conversation integration."""
# For relative imports to work in Python 3.6
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import logging
import traceback
import httpx
from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.util import ulid

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JARVIS from a config entry."""
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data[CONF_OPENAI_KEY_KEY]

    conversation.async_set_agent(hass, entry, JARVISAgent(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload JARVIS."""
    # hass.data[DOMAIN].pop(entry.entry_id)
    conversation.async_unset_agent(hass, entry)
    return True


class JARVISAgent(conversation.AbstractConversationAgent):
    """JARVIS conversation agent."""

    hass: HomeAssistant
    entry: ConfigEntry
    http_client: httpx.Client

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.http_client = httpx.Client(timeout=45)

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
            json_request = {
                "input": user_input.text,
                "config": {"configurable": {"session_id": conversation_id}},
            }
            _LOGGER.info(json_request)

            response = self.http_client.post(
                "http://192.168.10.20:10055/invoke",
                json=json_request,

            )
            response.raise_for_status()

            json_obj = response.json()
            _LOGGER.info(json_obj)

            last_msg_text = (
                json_obj.get("output")
                if response.status_code == 200
                else f"Sorry, I can't do that (got error {response.status_code})"
            )

            _LOGGER.info(f"msg: {last_msg_text}")
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
