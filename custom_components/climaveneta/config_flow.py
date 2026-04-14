"""Support for the Mitsubishi-Climaveneta iMXW and iLife2 fancoil series."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from homeassistant.const import CONF_NAME, CONF_SLAVE, DEVICE_DEFAULT_NAME

from .const import (
    CLIMAVENETA_ILIFE2,
    CLIMAVENETA_IMXW,
    CONF_HUB,
    DEFAULT_MODBUS_HUB,
    DEFAULT_SERIAL_SLAVE_ID,
    DEVICE_TYPE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ClimavenetaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc]
    """Handle a config flow for Climaveneta."""

    VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step when user initializes a integration."""
        errors: dict[Any, Any] = {}
        if user_input is not None:
            title_device = f"Climaveneta {user_input[DEVICE_TYPE]} {user_input[CONF_NAME]} at {user_input[CONF_HUB]}:{user_input[CONF_SLAVE]}"
            return self.async_create_entry(title=title_device, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(DEVICE_TYPE, default=CLIMAVENETA_IMXW): vol.In(
                    (
                        CLIMAVENETA_IMXW,
                        CLIMAVENETA_ILIFE2,
                    )
                ),
                vol.Required(CONF_HUB, default=str(DEFAULT_MODBUS_HUB)): str,
                vol.Required(CONF_SLAVE, default=int(DEFAULT_SERIAL_SLAVE_ID)): vol.All(
                    int, vol.Range(min=0, max=255)
                ),
                vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
