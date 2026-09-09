"""Config flow for the Temzit hydromodule."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .client import TemzitClient
from .const import (
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TemzitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a Temzit hydromodule."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """User initiated setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            client = TemzitClient(host, port)
            try:
                await client.get_actual_state()
            except Exception as err:  # noqa: BLE001 - surface any failure
                _LOGGER.warning("Temzit connection test failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=host,
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
