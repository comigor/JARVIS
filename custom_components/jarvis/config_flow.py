"""Config flow for Jarvis Conversation integration."""
from __future__ import annotations

import logging
import types
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_OPENAI_KEY_KEY,
    CONF_HA_KEY_KEY,
    CONF_HA_URL_KEY,
    CONF_GOOGLE_API_KEY,
    CONF_GOOGLE_CX_KEY,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPENAI_KEY_KEY): str,
        vol.Optional(CONF_HA_KEY_KEY): str,
        vol.Optional(CONF_HA_URL_KEY): str,
        vol.Optional(CONF_GOOGLE_API_KEY): str,
        vol.Optional(CONF_GOOGLE_CX_KEY): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO: validate
    pass

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jarvis Conversation."""

    VERSION = 5

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            await validate_input(self.hass, user_input)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title="J.A.R.V.I.S.", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """OpenAI config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="J.A.R.V.I.S.", data=user_input)
        schema = openai_config_option_schema(self.config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


DEFAULT_OPTIONS = types.MappingProxyType(
    {
        CONF_OPENAI_KEY_KEY: '',
        CONF_HA_KEY_KEY: '',
        CONF_HA_URL_KEY: '',
        CONF_GOOGLE_API_KEY: '',
        CONF_GOOGLE_CX_KEY: '',
    }
)

def openai_config_option_schema(options: MappingProxyType[str, Any]) -> dict:
    """Return a schema for OpenAI completion options."""
    if not options:
        options = DEFAULT_OPTIONS
    return {
        vol.Required(
            CONF_OPENAI_KEY_KEY,
            description={'suggested_value': options.get(CONF_OPENAI_KEY_KEY, '')},
        ): str,
        vol.Optional(
            CONF_HA_KEY_KEY,
            description={'suggested_value': options.get(CONF_HA_KEY_KEY, '')},
        ): str,
        vol.Optional(
            CONF_HA_URL_KEY,
            description={'suggested_value': options.get(CONF_HA_URL_KEY, '')},
            default=DEFAULT_HA_URL,
        ): str,
        vol.Optional(
            CONF_GOOGLE_API_KEY,
            description={'suggested_value': options.get(CONF_GOOGLE_API_KEY, '')},
        ): str,
        vol.Optional(
            CONF_GOOGLE_CX_KEY,
            description={'suggested_value': options.get(CONF_GOOGLE_CX_KEY, '')},
        ): str,
    }
