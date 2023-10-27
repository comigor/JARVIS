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
    DEFAULT_HA_URL,
    CONF_GOOGLE_API_KEY,
    CONF_GOOGLE_CX_KEY,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_OPENAI_KEY_KEY): str,
        vol.Optional(CONF_HA_KEY_KEY): str,
        vol.Optional(
            CONF_HA_URL_KEY,
            description={'suggested_value': 'http://127.0.0.1:8123'},
        ): str,
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

    VERSION = 4

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
