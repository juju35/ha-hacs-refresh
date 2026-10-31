"""HACS Refresh: check every repository downloaded with HACS for updates, on the server."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CALLBACK_TYPE, CoreState, Event, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    CARD_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_CHECK_REPOSITORY,
    SERVICE_CHECK_UPDATES,
    VERSION,
)
from .refresher import STORAGE_VERSION, HacsNotAvailableError, HacsRefresher

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BUTTON, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
ATTR_WAIT = "wait"
# Delay before trying again a scheduled check skipped because HACS couldn't be used.
RETRY_INTERVAL = timedelta(hours=1)
CHECK_UPDATES_SCHEMA = vol.Schema({vol.Optional(ATTR_WAIT, default=False): cv.boolean})
CHECK_REPOSITORY_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})

type HacsRefreshConfigEntry = ConfigEntry[HacsRefresher]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the card, load it on every dashboard, and register the actions (every user, like the button)."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(Path(__file__).parent / "frontend" / "hacs-refresh-card.js"), True)]
    )

    async def _register(_: Event | None = None) -> None:
        if not await _async_register_resource(hass):
            # Dashboard resources in YAML mode: load the card on every page instead.
            add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")

    if hass.state is CoreState.running:
        await _register()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register)

    def loaded_refresher() -> HacsRefresher:
        entries = [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
        return entries[0].runtime_data

    async def check_updates(call: ServiceCall) -> None:
        refresher = loaded_refresher()
        try:
            refresher.async_start()
        except HacsNotAvailableError as err:
            raise _validation_error(err) from err
        if call.data[ATTR_WAIT]:
            await refresher.async_wait()
            # Like check_repository: fail when the check failed or could not check some repositories.
            refresher.raise_for_result()

    hass.services.async_register(DOMAIN, SERVICE_CHECK_UPDATES, check_updates, CHECK_UPDATES_SCHEMA)

    async def check_repository(call: ServiceCall) -> None:
        try:
            await loaded_refresher().async_check_repositories(call.data[ATTR_ENTITY_ID])
        except HacsNotAvailableError as err:
            raise _validation_error(err) from err

    hass.services.async_register(DOMAIN, SERVICE_CHECK_REPOSITORY, check_repository, CHECK_REPOSITORY_SCHEMA)
    return True


def _validation_error(err: HacsNotAvailableError) -> ServiceValidationError:
    """The same translated message, as a validation error of the action."""
    return ServiceValidationError(
        translation_domain=err.translation_domain,
        translation_key=err.translation_key,
        translation_placeholders=err.translation_placeholders,
    )


def _storage_resources(hass: HomeAssistant) -> Any | None:
    """Return the dashboard resources collection when it is editable from the UI.

    hass.data["lovelace"] is a dict before 2025.2, then a dataclass whose `mode` field became `resource_mode` in 2026.2.
    """
    lovelace = hass.data.get("lovelace")
    if isinstance(lovelace, dict):
        mode, resources = lovelace.get("resource_mode", lovelace.get("mode")), lovelace.get("resources")
    else:
        mode = getattr(lovelace, "resource_mode", getattr(lovelace, "mode", None))
        resources = getattr(lovelace, "resources", None)
    return resources if mode == "storage" else None


async def _async_register_resource(hass: HomeAssistant) -> bool:
    """Add or update the card in Settings → Dashboards → Resources."""
    resources = _storage_resources(hass)
    if resources is None:
        return False
    url = f"{CARD_URL}?v={VERSION}"
    try:
        await resources.async_get_info()  # loads the collection from storage
        existing = [item for item in resources.async_items() if item.get("url", "").split("?")[0] == CARD_URL]
        if not existing:
            await resources.async_create_item({"res_type": "module", "url": url})
            return True
        if existing[0]["url"] != url:
            await resources.async_update_item(existing[0]["id"], {"res_type": "module", "url": url})
        for duplicate in existing[1:]:
            await resources.async_delete_item(duplicate["id"])
    except Exception:  # noqa: BLE001 - never block the integration on the card
        _LOGGER.exception("Could not register the HACS Refresh card as a dashboard resource")
        return False
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> bool:
    if hass.state is CoreState.running:
        # async_setup runs once per start: after the entry was removed (which drops the card resource) and
        # added again, the resource has to come back without a restart.
        await _async_register_resource(hass)
    refresher = HacsRefresher(hass, entry)
    await refresher.async_load()
    entry.runtime_data = refresher

    hours = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    if hours > 0:
        _async_schedule(hass, entry, refresher, timedelta(hours=hours))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


def _async_schedule(
    hass: HomeAssistant, entry: HacsRefreshConfigEntry, refresher: HacsRefresher, interval: timedelta
) -> None:
    """Run the automatic check one interval after the last one, kept across restarts.

    Once Home Assistant has started, an overdue check runs right away, so that restarting more
    often than the interval doesn't postpone it forever. Before the first check, the interval
    counts from the first setup.
    """
    cancel: list[CALLBACK_TYPE] = []

    @callback
    def cancel_timer() -> None:
        while cancel:
            cancel.pop()()

    @callback
    def schedule(delay: timedelta) -> None:
        cancel_timer()
        cancel.append(async_call_later(hass, max(delay.total_seconds(), 0), run))

    def remaining() -> timedelta:
        last = refresher.last_check or refresher.since or dt_util.utcnow()
        return last + interval - dt_util.utcnow()

    @callback
    def schedule_next() -> None:
        schedule(remaining())

    async def run(_now: datetime) -> None:
        cancel.clear()
        # When a check is already running, its end (on_done) schedules the next one.
        try:
            refresher.async_start()
        except HacsNotAvailableError as err:
            _LOGGER.warning("Scheduled HACS check skipped: %s", err)
            # Often temporary (HACS rate-limited or still starting): try again within the hour.
            schedule(min(interval, RETRY_INTERVAL))

    @callback
    def at_started(_hass: HomeAssistant) -> None:
        if remaining() <= timedelta(0):
            entry.async_create_task(hass, run(dt_util.utcnow()))
        else:
            schedule_next()

    refresher.on_done = schedule_next
    entry.async_on_unload(cancel_timer)
    entry.async_on_unload(async_at_started(hass, at_started))


async def async_unload_entry(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> None:
    """Forget the last check and drop the card resource when the integration is removed."""
    await Store(hass, STORAGE_VERSION, DOMAIN).async_remove()
    if (resources := _storage_resources(hass)) is None:
        return
    for item in list(resources.async_items()):
        if item.get("url", "").split("?")[0] == CARD_URL:
            await resources.async_delete_item(item["id"])


async def _async_reload(hass: HomeAssistant, entry: HacsRefreshConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
