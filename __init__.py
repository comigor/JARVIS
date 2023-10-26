"""The OpenAI Conversation integration."""
from __future__ import annotations

from functools import partial
import logging
from typing import Literal, Annotated

import openai
from openai import error
import voluptuous as vol

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    TemplateError,
)
from homeassistant.helpers import config_validation as cv, intent, selector, template, area_registry as ar
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import ulid
import json
import traceback

from kani import AIParam, Kani, ai_function, ChatMessage
from kani.engines.openai import OpenAIEngine

from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_CHAT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DOMAIN,
    HOME_INFO_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)
SERVICE_GENERATE_IMAGE = "generate_image"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up OpenAI Conversation."""

    async def render_image(call: ServiceCall) -> ServiceResponse:
        """Render an image with dall-e."""
        try:
            response = await openai.Image.acreate(
                api_key=hass.data[DOMAIN][call.data["config_entry"]],
                prompt=call.data["prompt"],
                n=1,
                size=f'{call.data["size"]}x{call.data["size"]}',
            )
        except error.OpenAIError as err:
            raise HomeAssistantError(f"Error generating image: {err}") from err

        return response["data"][0]

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_IMAGE,
        render_image,
        schema=vol.Schema(
            {
                vol.Required("config_entry"): selector.ConfigEntrySelector(
                    {
                        "integration": DOMAIN,
                    }
                ),
                vol.Required("prompt"): cv.string,
                vol.Optional("size", default="512"): vol.In(("256", "512", "1024")),
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenAI Conversation from a config entry."""
    try:
        await hass.async_add_executor_job(
            partial(
                openai.Engine.list,
                api_key=entry.data[CONF_API_KEY],
                request_timeout=10,
            )
        )
    except error.AuthenticationError as err:
        _LOGGER.error("Invalid API key: %s", err)
        return False
    except error.OpenAIError as err:
        raise ConfigEntryNotReady(err) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data[CONF_API_KEY]

    conversation.async_set_agent(hass, entry, OpenAIAgent(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload OpenAI."""
    hass.data[DOMAIN].pop(entry.entry_id)
    conversation.async_unset_agent(hass, entry)
    return True


class MyKani(Kani):
    @ai_function()
    def get_weather(
        self,
        location: Annotated[str, AIParam(desc="The city and state, e.g. San Francisco, CA")],
    ):
        """Get the current weather in a given location."""
        return f"Weather in {location}: Sunny, 27 degrees celsius."

    # @ai_function()
    # def call_hass(
    #     self,
    #     location: Annotated[str, AIParam(desc="The city and state, e.g. San Francisco, CA")],
    # ):
    #     """Get the current weather in a given location."""
    #     await self.hass.services.async_call(
    #         response_json["command"]["domain"],
    #         response_json["command"]["service"],
    #         response_json["command"]["data"],
    #     )
    #     return f"Weather in {location}: Sunny, 27 degrees celsius."


class OpenAIAgent(conversation.AbstractConversationAgent):
    """OpenAI conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.history: dict[str, list[dict]] = {}

        self.engine = None
        self.ai = None

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    def setup_ai(self):
        self.engine = OpenAIEngine(self.entry.data[CONF_API_KEY], model="gpt-3.5-turbo-0613", max_context_size=4096)

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        raw_prompt = self.entry.options.get(CONF_PROMPT, DEFAULT_PROMPT)
        model = self.entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        max_tokens = self.entry.options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        top_p = self.entry.options.get(CONF_TOP_P, DEFAULT_TOP_P)
        temperature = self.entry.options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)

        new_message = ChatMessage.user(user_input.text + ". Answer in syntactically perfect json and only json.")

        if user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id] + [new_message]
        else:
            conversaton_id = ulid.ulid()

            try:
                home_info_prompt = self._async_generate_prompt(HOME_INFO_TEMPLATE)
            except TemplateError as err:
                _LOGGER.error("Error rendering prompt: %s", err)
                intent_response = intent.IntentResponse(language=user_input.language)
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    f"Sorry, I had a problem with my template: {err}\n{traceback.format_exc()}",
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversaton_id
                )

            _LOGGER.info('PROMPTERS:')
            _LOGGER.info(home_info_prompt)

            chat_history = [
                ChatMessage.user(home_info_prompt),
                ChatMessage.assistant('{"comment":"Got it!"}'),
            ]

            if self.ai == None:
                await self.hass.async_add_executor_job(self.setup_ai)
                self.ai = MyKani(
                    self.engine,
                    system_prompt=ChatMessage.system(raw_prompt),
                    chat_history=chat_history,
                )

        try:
            _LOGGER.info('FULL ROUND:')
            async for msg in self.ai.full_round(user_input.text + ". Answer in syntactically perfect json and only json."):
                _LOGGER.info(msg)
                _LOGGER.info(msg.text)
        except error.OpenAIError as err:
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem talking to OpenAI: {err}\n{traceback.format_exc()}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech('ok')

        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    def _async_generate_prompt(self, raw_prompt: str) -> str:
        _LOGGER.info('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        _LOGGER.info(ar.async_get(self.hass))
        _LOGGER.info(list(ar.async_get(self.hass).areas.values()))

        """Generate a prompt for the user."""
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
                "areas": list(ar.async_get(self.hass).areas.values()),
            },
            parse_result=False,
        )
