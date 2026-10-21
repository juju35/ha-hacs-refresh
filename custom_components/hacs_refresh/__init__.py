"""HACS Refresh: check every repository downloaded with HACS for updates, on the server."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, SERVICE_CHECK_UPDATES
from .refresher import HacsNotAvailableError, HacsRefresher

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BUTTON, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
ATTR_WAIT = "wait"
CHECK_UPDATES_SCHEMA = vol.Schema({vol.Optional(ATTR_WAIT, default=False): cv.boolean})

type HacsRefreshConfigEntry = ConfigEntry[HacsRefresher]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the action once, for administrators only."""

    async def check_updates(call: ServiceCall) -> None:
        entries = [
            e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED
        ]
        if not entries:
            raise ServiceValidationError("HACS Refresh is not loaded")
        refresher: HacsRefresher = entries[0].runtime_data
        try:
            refresher.async_start()
        except HacsNotAvailableError as err:
            raise ServiceValidationError(str(err)) from err
        if call.data[ATTR_WAIT]:
            await refresher.async_wait()

    async_register_admin_service(
        hass, DOMAIN, SERVICE_CHECK_UPDATES, check_updates, CHECK_UPDATES_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> bool:
    refresher = HacsRefresher(hass)
    entry.runtime_data = refresher

    hours = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    if hours > 0:

        async def scheduled(_now: datetime) -> None:
            try:
                refresher.async_start()
            except HacsNotAvailableError as err:
                _LOGGER.warning("Scheduled HACS check skipped: %s", err)

        entry.async_on_unload(async_track_time_interval(hass, scheduled, timedelta(hours=hours)))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
