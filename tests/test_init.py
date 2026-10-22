"""Tests for HACS Refresh."""

from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.hacs_refresh.const import CONF_SCAN_INTERVAL, DOMAIN

from .conftest import make_repo

STATUS = "sensor.hacs_refresh_status"
LAST_CHECK = "sensor.hacs_refresh_last_check"
BUTTON = "button.hacs_refresh_check_for_updates"


async def _setup(hass: HomeAssistant, hours: int = 24) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, options={CONF_SCAN_INTERVAL: hours})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow(hass, fake_hacs):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 12})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {CONF_SCAN_INTERVAL: 12}


async def test_config_flow_without_hacs(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "hacs_not_loaded"


async def test_options_flow_changes_interval(hass, fake_hacs):
    entry = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 6})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options == {CONF_SCAN_INTERVAL: 6}
    assert entry.state is ConfigEntryState.LOADED


async def test_check_updates_action(hass, fake_hacs):
    await _setup(hass)
    assert hass.states.get(STATUS).state == "idle"
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    await hass.async_block_till_done()

    for repo in fake_hacs.repositories.list_downloaded:
        repo.update_repository.assert_awaited_once_with(ignore_issues=True, force=True)
    fake_hacs.data.async_write.assert_awaited_once()
    for coordinator in fake_hacs.coordinators.values():
        coordinator.async_update_listeners.assert_called_once()

    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["done"] == 3
    assert state.attributes["total"] == 3
    assert state.attributes["updates"] == 1
    assert state.attributes["failed"] == []
    assert hass.states.get(LAST_CHECK).state not in ("unknown", "unavailable")


async def test_button_and_failed_repository(hass, fake_hacs):
    fake_hacs.repositories.list_downloaded.append(make_repo("someone/broken", fail=True))
    entry = await _setup(hass)
    await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)
    # The check runs as a background task, which async_block_till_done doesn't wait for.
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["done"] == 4
    assert state.attributes["failed"] == ["someone/broken"]


async def test_scheduled_check(hass, fake_hacs):
    entry = await _setup(hass, hours=2)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=2, seconds=1))
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    fake_hacs.repositories.list_downloaded[0].update_repository.assert_awaited_once()


async def test_scheduled_check_disabled(hass, fake_hacs):
    await _setup(hass, hours=0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(days=10))
    await hass.async_block_till_done()
    fake_hacs.repositories.list_downloaded[0].update_repository.assert_not_awaited()


async def test_hacs_disabled(hass, fake_hacs):
    await _setup(hass)
    fake_hacs.system.disabled = True
    fake_hacs.system.disabled_reason = "rate_limit"
    with pytest.raises(ServiceValidationError, match="disabled"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_unsupported_hacs_version(hass, fake_hacs):
    await _setup(hass)
    del fake_hacs.coordinators
    with pytest.raises(ServiceValidationError, match="not supported"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


def _hacs_update_entity(hass: HomeAssistant, repo, platform: str = "hacs") -> str:
    """Register the update entity HACS creates for a repository (unique_id = repository id)."""
    entry = er.async_get(hass).async_get_or_create(
        "update", platform, str(repo.data.id), suggested_object_id=repo.data.full_name.split("/")[1]
    )
    return entry.entity_id


async def test_check_repository(hass, fake_hacs):
    await _setup(hass)
    parcel = fake_hacs.repositories.list_downloaded[1]
    entity_id = _hacs_update_entity(hass, parcel)
    await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)

    parcel.update_repository.assert_awaited_once_with(ignore_issues=True, force=True)
    fake_hacs.repositories.list_downloaded[0].update_repository.assert_not_awaited()
    fake_hacs.data.async_write.assert_awaited_once()
    fake_hacs.coordinators["integration"].async_update_listeners.assert_called_once()
    fake_hacs.coordinators["plugin"].async_update_listeners.assert_not_called()
    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["checking"] == []
    # A single repository is not a full check.
    assert hass.states.get(LAST_CHECK).state == "unknown"


async def test_check_repository_rejects_other_entities(hass, fake_hacs):
    await _setup(hass)
    other = _hacs_update_entity(hass, fake_hacs.repositories.list_downloaded[0], platform="demo")
    with pytest.raises(ServiceValidationError, match="not a HACS update entity"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": other}, blocking=True)
    with pytest.raises(ServiceValidationError, match="not a HACS update entity"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": "update.missing"}, blocking=True)


async def test_check_repository_failure(hass, fake_hacs):
    broken = make_repo("someone/broken", fail=True)
    fake_hacs.repositories.list_downloaded.append(broken)
    await _setup(hass)
    entity_id = _hacs_update_entity(hass, broken)
    with pytest.raises(HomeAssistantError, match="someone/broken"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    assert hass.states.get(STATUS).attributes["checking"] == []
