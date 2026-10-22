"""Config flow for HACS Refresh: a single entry, the check interval in the options."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, HACS_DOMAIN, MAX_SCAN_INTERVAL


def _interval_schema(default: int) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SCAN_INTERVAL, default=default): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=MAX_SCAN_INTERVAL,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="h",
                )
            )
        }
    )


class HacsRefreshConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if HACS_DOMAIN not in self.hass.config.components:
            return self.async_abort(reason="hacs_not_loaded")
        if user_input is not None:
            return self.async_create_entry(
                title="HACS Refresh",
                data={},
                options={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
            )
        return self.async_show_form(step_id="user", data_schema=_interval_schema(DEFAULT_SCAN_INTERVAL))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HacsRefreshOptionsFlow()


class HacsRefreshOptionsFlow(OptionsFlow):
    """Change the interval between two automatic checks."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])})
        current = int(self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        return self.async_show_form(step_id="init", data_schema=_interval_schema(current))
