"""Tests for Marketplace Refresh."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.marketplace_refresh.const import CARD_URL, CONF_SCAN_INTERVAL, DOMAIN

from .conftest import make_repo

STATUS = "sensor.marketplace_refresh_status"
LAST_CHECK = "sensor.marketplace_refresh_last_check"
BUTTON = "button.marketplace_refresh_check_for_updates"


async def _setup(hass: HomeAssistant, hours: int = 24) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, options={CONF_SCAN_INTERVAL: hours})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow(hass, fake_marketplace):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 12})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == {CONF_SCAN_INTERVAL: 12}


async def test_config_flow_without_marketplace(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "marketplace_not_loaded"


async def test_options_flow_changes_interval(hass, fake_marketplace):
    entry = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(result["flow_id"], {CONF_SCAN_INTERVAL: 6})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options == {CONF_SCAN_INTERVAL: 6}
    assert entry.state is ConfigEntryState.LOADED


async def test_check_updates_action(hass, fake_marketplace):
    await _setup(hass)
    assert hass.states.get(STATUS).state == "idle"
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    await hass.async_block_till_done()

    for repo in fake_marketplace.repositories.list_installed:
        repo.update_repository.assert_awaited_once_with(ignore_issues=True, force=True)
    fake_marketplace.data.async_write.assert_awaited_once()
    for coordinator in fake_marketplace.coordinators.values():
        coordinator.async_update_listeners.assert_called_once()

    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["done"] == 3
    assert state.attributes["total"] == 3
    assert state.attributes["updates"] == 1
    assert state.attributes["failed"] == []
    assert hass.states.get(LAST_CHECK).state not in ("unknown", "unavailable")


async def test_button_and_failed_repository(hass, fake_marketplace):
    fake_marketplace.repositories.list_installed.append(make_repo("someone/broken", fail=True))
    entry = await _setup(hass)
    await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)
    # The check runs as a background task, which async_block_till_done doesn't wait for.
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["done"] == 4
    assert state.attributes["failed"] == ["someone/broken"]


async def test_scheduled_check(hass, fake_marketplace):
    entry = await _setup(hass, hours=2)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(hours=2, seconds=1))
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    fake_marketplace.repositories.list_installed[0].update_repository.assert_awaited_once()


async def test_scheduled_check_disabled(hass, fake_marketplace):
    await _setup(hass, hours=0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(days=10))
    await hass.async_block_till_done()
    fake_marketplace.repositories.list_installed[0].update_repository.assert_not_awaited()


async def test_marketplace_disabled(hass, fake_marketplace):
    await _setup(hass)
    fake_marketplace.system.disabled = True
    fake_marketplace.system.disabled_reason = "rate_limit"
    with pytest.raises(ServiceValidationError, match="disabled"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_unsupported_marketplace_version(hass, fake_marketplace):
    await _setup(hass)
    del fake_marketplace.coordinators
    with pytest.raises(ServiceValidationError, match="not supported"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


def _marketplace_update_entity(hass: HomeAssistant, repo, platform: str = "marketplace") -> str:
    """Register the update entity the Marketplace creates for a repository (unique_id = repository id)."""
    entry = er.async_get(hass).async_get_or_create(
        "update", platform, str(repo.data.id), suggested_object_id=repo.data.full_name.split("/")[1]
    )
    return entry.entity_id


async def test_check_repository(hass, fake_marketplace):
    await _setup(hass)
    parcel = fake_marketplace.repositories.list_installed[1]
    entity_id = _marketplace_update_entity(hass, parcel)
    await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)

    parcel.update_repository.assert_awaited_once_with(ignore_issues=True, force=True)
    fake_marketplace.repositories.list_installed[0].update_repository.assert_not_awaited()
    fake_marketplace.data.async_write.assert_awaited_once()
    fake_marketplace.coordinators["integration"].async_update_listeners.assert_called_once()
    fake_marketplace.coordinators["plugin"].async_update_listeners.assert_not_called()
    state = hass.states.get(STATUS)
    assert state.state == "idle"
    assert state.attributes["checking"] == []
    # A single repository is not a full check.
    assert hass.states.get(LAST_CHECK).state == "unknown"


async def test_check_repository_rejects_other_entities(hass, fake_marketplace):
    await _setup(hass)
    other = _marketplace_update_entity(hass, fake_marketplace.repositories.list_installed[0], platform="demo")
    with pytest.raises(ServiceValidationError, match="not a Marketplace update entity"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": other}, blocking=True)
    with pytest.raises(ServiceValidationError, match="not a Marketplace update entity"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": "update.missing"}, blocking=True)


async def test_check_repository_failure(hass, fake_marketplace):
    broken = make_repo("someone/broken", fail=True)
    fake_marketplace.repositories.list_installed.append(broken)
    await _setup(hass)
    entity_id = _marketplace_update_entity(hass, broken)
    with pytest.raises(HomeAssistantError, match="someone/broken"):
        await hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    assert hass.states.get(STATUS).attributes["checking"] == []


async def test_overdue_check_runs_at_startup(hass, fake_marketplace, hass_storage):
    """A restart doesn't postpone the automatic check: an overdue one runs once Home Assistant has started."""
    last = dt_util.utcnow() - timedelta(hours=25)
    hass_storage[DOMAIN] = {"version": 1, "key": DOMAIN, "data": {"last_check": last.isoformat(), "updates": 2}}
    entry = await _setup(hass)
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    fake_marketplace.repositories.list_installed[0].update_repository.assert_awaited_once()
    assert hass_storage[DOMAIN]["data"]["updates"] == 1
    assert dt_util.parse_datetime(hass_storage[DOMAIN]["data"]["last_check"]) > last


async def test_recent_check_is_restored_and_next_one_kept(hass, fake_marketplace, hass_storage, freezer):
    last = dt_util.utcnow() - timedelta(hours=20)
    hass_storage[DOMAIN] = {"version": 1, "key": DOMAIN, "data": {"last_check": last.isoformat(), "updates": 2}}
    entry = await _setup(hass)
    repo = fake_marketplace.repositories.list_installed[0]
    repo.update_repository.assert_not_awaited()
    assert hass.states.get(STATUS).attributes["updates"] == 2
    assert dt_util.parse_datetime(hass.states.get(LAST_CHECK).state) == last.replace(microsecond=0)
    # 24 h after the last check, i.e. 4 h after this start, not 24 h after it.
    freezer.tick(timedelta(hours=3, minutes=59))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    freezer.tick(timedelta(minutes=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    repo.update_repository.assert_awaited_once()
    # Then again one interval after this check.
    freezer.tick(timedelta(hours=24, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    assert repo.update_repository.await_count == 2


async def test_first_install_waits_one_interval(hass, fake_marketplace, hass_storage, freezer):
    entry = await _setup(hass, hours=2)
    repo = fake_marketplace.repositories.list_installed[0]
    repo.update_repository.assert_not_awaited()
    assert hass_storage[DOMAIN]["data"]["since"]
    # Restarted an hour later: still counts from the first setup.
    assert await hass.config_entries.async_reload(entry.entry_id)
    freezer.tick(timedelta(hours=1, minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    repo.update_repository.assert_awaited_once()


async def test_unload_cancels_running_check(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_marketplace.repositories.list_installed[0].update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    old = entry.runtime_data
    assert old.async_start()
    await hass.async_block_till_done()
    assert old.running
    task = old._task
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert task.cancelled()
    fake_marketplace.data.async_write.assert_not_awaited()
    release.set()


async def test_check_updates_open_to_non_admin(hass, fake_marketplace, hass_read_only_user):
    """Like the button, which runs the same check, the action is open to every user."""
    await _setup(hass, hours=0)
    await hass.services.async_call(
        DOMAIN, "check_updates", {"wait": True}, blocking=True, context=Context(user_id=hass_read_only_user.id)
    )
    fake_marketplace.repositories.list_installed[0].update_repository.assert_awaited_once()


async def test_marketplace_disabled_without_reason(hass, fake_marketplace):
    """A Marketplace version without disabled_reason still gives the clear error."""
    await _setup(hass)
    fake_marketplace.system.disabled = True
    del fake_marketplace.system.disabled_reason
    with pytest.raises(ServiceValidationError, match="Marketplace is disabled"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_check_repository_waits_for_full_check(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    assert entry.runtime_data.async_start()
    await hass.async_block_till_done()
    call = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert not call.done()
    release.set()
    async with asyncio.timeout(5):
        await call
    # Refreshed once, by the full check only.
    parcel.update_repository.assert_awaited_once()
    assert not entry.runtime_data.running


async def test_check_repository_skips_entity_already_checking(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    first = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert hass.states.get(STATUS).attributes["checking"] == [entity_id]
    second = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    # The second call waits for the result of the first one instead of returning before it.
    assert not second.done()
    release.set()
    async with asyncio.timeout(5):
        await first
        await second
    parcel.update_repository.assert_awaited_once()
    fake_marketplace.data.async_write.assert_awaited_once()


async def _await_service(call: asyncio.Task) -> None:
    """Await a service call task; a raw CancelledError (the caller was not cancelled) fails the test."""
    try:
        async with asyncio.timeout(5):
            await call
    except asyncio.CancelledError:
        pytest.fail("the action ended with a raw CancelledError")


async def test_waiting_check_updates_fails_cleanly_on_unload(hass, fake_marketplace):
    """Unloading the entry cancels the check: an action waiting for it gets a Home Assistant error."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_marketplace.repositories.list_installed[0].update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    call = hass.async_create_task(hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True))
    await asyncio.sleep(0.01)
    assert not call.done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(HomeAssistantError, match="cancelled"):
        await _await_service(call)
    release.set()


async def test_waiting_check_repository_fails_cleanly_on_unload(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    assert entry.runtime_data.async_start()
    await hass.async_block_till_done()
    call = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(HomeAssistantError, match="cancelled"):
        await _await_service(call)
    release.set()


async def test_full_check_waits_for_running_check_repository(hass, fake_marketplace):
    """A full check started while check_repository runs doesn't refresh that repository a second time."""
    release = asyncio.Event()
    running = 0
    most = 0

    async def slow(**_kwargs):
        nonlocal running, most
        running += 1
        most = max(most, running)
        await release.wait()
        running -= 1

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    single = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert entry.runtime_data.async_start()
    await asyncio.sleep(0.01)
    # The other repositories are checked, the full check waits for this one.
    # (The refresher's counter, not the sensor's attribute: progress notifications are throttled.)
    assert entry.runtime_data.done == 2
    release.set()
    await _await_service(single)
    async with asyncio.timeout(5):
        await entry.runtime_data.async_wait()
    assert most == 1
    parcel.update_repository.assert_awaited_once()
    state = hass.states.get(STATUS)
    assert state.attributes["done"] == 3
    assert state.attributes["failed"] == []


async def test_full_check_reports_failure_of_awaited_check_repository(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    single = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert entry.runtime_data.async_start()
    release.set()
    with pytest.raises(HomeAssistantError, match="juju35/ha-parcel"):
        await _await_service(single)
    async with asyncio.timeout(5):
        await entry.runtime_data.async_wait()
    assert hass.states.get(STATUS).attributes["failed"] == ["juju35/ha-parcel"]
    parcel.update_repository.assert_awaited_once()


async def test_second_check_repository_waits_for_the_first(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    first = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    second = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    assert not second.done()
    release.set()
    # Both report the failure of the one refresh.
    for call in (first, second):
        with pytest.raises(HomeAssistantError, match="juju35/ha-parcel"):
            await _await_service(call)
    parcel.update_repository.assert_awaited_once()


async def test_check_repository_during_failing_full_check(hass, fake_marketplace):
    """check_repository waiting for a full check fails when that check couldn't check its repository."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    other = _marketplace_update_entity(hass, fake_marketplace.repositories.list_installed[0])
    assert entry.runtime_data.async_start()
    await hass.async_block_till_done()
    failing = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    fine = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": other}, blocking=True)
    )
    await asyncio.sleep(0.01)
    release.set()
    with pytest.raises(HomeAssistantError, match="juju35/ha-parcel"):
        await _await_service(failing)
    await _await_service(fine)


async def test_check_repository_during_full_check_in_error(hass, fake_marketplace):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    fake_marketplace.data.async_write.side_effect = OSError("disk full")
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    assert entry.runtime_data.async_start()
    await hass.async_block_till_done()
    call = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    release.set()
    with pytest.raises(HomeAssistantError, match="disk full"):
        await _await_service(call)
    assert hass.states.get(STATUS).state == "error"


async def test_check_repository_calls_cancelled_together(hass, fake_marketplace):
    """Two check_repository calls on one repository, cancelled in the same tick, both get CancelledError."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    refresher = entry.runtime_data
    first = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    second = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    first.cancel()
    second.cancel()
    for call in (first, second):
        with pytest.raises(asyncio.CancelledError):
            await call
    release.set()


async def test_full_check_cancelled_with_awaited_check_repository(hass, fake_marketplace):
    """A full check cancelled together with the check_repository it waits for stops, without refreshing again."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    refresher = entry.runtime_data
    single = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    assert refresher.async_start()
    await asyncio.sleep(0.01)
    task = refresher._task
    single.cancel()
    task.cancel()
    await asyncio.sleep(0.01)
    assert task.done()
    parcel.update_repository.assert_awaited_once()
    async with asyncio.timeout(1):
        assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(asyncio.CancelledError):
        await single
    release.set()


async def test_check_repository_checks_itself_when_the_awaited_call_is_cancelled(hass, fake_marketplace):
    """A check_repository waiting for another call's result checks the repository itself if that call is cancelled."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    refresher = entry.runtime_data
    first = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    second = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    await asyncio.sleep(0.01)
    assert not second.done()
    assert parcel.update_repository.await_count == 2
    release.set()
    async with asyncio.timeout(5):
        await second
    assert entry.state is ConfigEntryState.LOADED
    assert refresher._single == {}


async def test_waiting_check_repository_sees_the_write_failure(hass, fake_marketplace):
    """A check_repository waiting for another call must not report success when the Marketplace data write fails."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_marketplace.repositories.list_installed[1]
    parcel.update_repository.side_effect = slow
    fake_marketplace.data.async_write.side_effect = OSError("disk full")
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, parcel)
    refresher = entry.runtime_data
    first = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    second = hass.async_create_task(refresher.async_check_repositories([entity_id]))
    await asyncio.sleep(0.01)
    release.set()
    # The first call fails on the write; the second checks the repository itself and fails on it too.
    for call in (first, second):
        with pytest.raises(OSError, match="disk full"):
            async with asyncio.timeout(5):
                await call
    assert refresher._single == {}


async def test_check_updates_wait_fails_on_failed_repository(hass, fake_marketplace):
    """With wait: true, the action fails like check_repository when a repository could not be checked."""
    fake_marketplace.repositories.list_installed.append(make_repo("someone/broken", fail=True))
    await _setup(hass, hours=0)
    with pytest.raises(HomeAssistantError, match="someone/broken"):
        await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    # Without wait, the action only starts the check.
    await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_check_updates_wait_fails_when_full_check_fails(hass, fake_marketplace):
    fake_marketplace.data.async_write.side_effect = OSError("disk full")
    await _setup(hass, hours=0)
    with pytest.raises(HomeAssistantError, match="disk full"):
        await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    assert hass.states.get(STATUS).state == "error"


async def test_failed_attribute_is_a_copy(hass, fake_marketplace):
    """The published `failed` attribute is not the list the running check appends to."""
    fake_marketplace.repositories.list_installed.append(make_repo("someone/broken", fail=True))
    entry = await _setup(hass, hours=0)
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=False)
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    failed = hass.states.get(STATUS).attributes["failed"]
    assert failed == ["someone/broken"]
    assert failed is not entry.runtime_data.failed


async def test_skipped_scheduled_check_retried_within_the_hour(hass, fake_marketplace, freezer):
    """A scheduled check skipped because the Marketplace is disabled is retried after an hour, not a full interval."""
    entry = await _setup(hass, hours=24)
    repo = fake_marketplace.repositories.list_installed[0]
    fake_marketplace.system.disabled = True
    fake_marketplace.system.disabled_reason = "rate_limit"
    freezer.tick(timedelta(hours=24, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    fake_marketplace.system.disabled = False
    freezer.tick(timedelta(minutes=59))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    freezer.tick(timedelta(minutes=1, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    repo.update_repository.assert_awaited_once()


async def test_marketplace_disabled_without_reason_has_no_placeholder(hass, fake_marketplace):
    await _setup(hass)
    fake_marketplace.system.disabled = True
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)
    assert err.value.translation_key == "marketplace_disabled_unknown"
    assert "unknown" not in str(err.value)


async def test_check_repository_during_full_check_outside_its_categories(hass, fake_marketplace):
    """A repository whose category the full check leaves out is checked by check_repository itself."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_marketplace.repositories.list_installed[1].update_repository.side_effect = slow
    script = make_repo("someone/script", category="python_script")
    fake_marketplace.repositories.list_installed.append(script)
    entry = await _setup(hass, hours=0)
    entity_id = _marketplace_update_entity(hass, script)
    assert entry.runtime_data.async_start()
    await hass.async_block_till_done()
    call = hass.async_create_task(
        hass.services.async_call(DOMAIN, "check_repository", {"entity_id": entity_id}, blocking=True)
    )
    await asyncio.sleep(0.01)
    script.update_repository.assert_not_awaited()
    release.set()
    await _await_service(call)
    script.update_repository.assert_awaited_once_with(ignore_issues=True, force=True)


def _resources(hass: HomeAssistant):
    """The Lovelace resources collection: hass.data["lovelace"] is a dict before 2025.2, a dataclass after."""
    lovelace = hass.data["lovelace"]
    return lovelace["resources"] if isinstance(lovelace, dict) else lovelace.resources


def _card_urls(resources) -> list[str]:
    return [i["url"] for i in resources.async_items() if i["url"].split("?")[0] == CARD_URL]


async def test_next_check_for_the_card(hass, fake_marketplace):
    """The last check sensor gives the interval and when the next automatic check is due."""
    await _setup(hass, hours=6)
    attrs = hass.states.get(LAST_CHECK).attributes
    assert attrs["scan_interval"] == 6
    # Before the first check, the interval counts from the first setup.
    due = dt_util.parse_datetime(attrs["next_check"])
    assert timedelta(hours=5, minutes=59) < due - dt_util.utcnow() <= timedelta(hours=6)
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    await hass.async_block_till_done()
    state = hass.states.get(LAST_CHECK)
    # The timestamp state is rounded to the second.
    due = dt_util.parse_datetime(state.attributes["next_check"]).replace(microsecond=0)
    assert due == dt_util.parse_datetime(state.state) + timedelta(hours=6)


async def test_next_check_when_automatic_check_is_off(hass, fake_marketplace):
    await _setup(hass, hours=0)
    attrs = hass.states.get(LAST_CHECK).attributes
    assert attrs["scan_interval"] == 0
    assert attrs["next_check"] is None


async def test_card_is_served(hass, fake_marketplace, hass_client):
    await _setup(hass)
    client = await hass_client()
    response = await client.get(CARD_URL)
    assert response.status == 200
    assert "marketplace-refresh-card" in await response.text()


async def test_card_resource_back_after_remove_and_add(hass, fake_marketplace):
    """Removing the entry drops the card resource; adding it again without a restart brings it back."""
    assert await async_setup_component(hass, "lovelace", {})
    resources = _resources(hass)
    entry = await _setup(hass)
    assert len(_card_urls(resources)) == 1

    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _card_urls(resources) == []

    await _setup(hass)
    assert len(_card_urls(resources)) == 1


@pytest.mark.parametrize(
    ("key", "container"),
    [("mode", dict), ("resource_mode", dict), ("mode", SimpleNamespace), ("resource_mode", SimpleNamespace)],
)
async def test_card_resource_with_lovelace_data_variants(hass, fake_marketplace, key: str, container: type):
    """hass.data["lovelace"]: a dict before 2025.2, then a dataclass with `mode`, renamed `resource_mode` in 2026.2."""
    assert await async_setup_component(hass, "lovelace", {})
    resources = _resources(hass)
    hass.data["lovelace"] = container(**{key: "storage", "resources": resources, "dashboards": {}})
    entry = await _setup(hass)
    assert len(_card_urls(resources)) == 1
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _card_urls(resources) == []


async def test_card_resource_yaml_mode_untouched(hass, fake_marketplace):
    """Resources in YAML mode are not edited (the card is loaded on every page instead)."""
    from homeassistant.components.lovelace.resources import ResourceYAMLCollection

    assert await async_setup_component(hass, "lovelace", {})
    hass.data["lovelace"] = {"mode": "yaml", "resources": ResourceYAMLCollection([]), "dashboards": {}}
    with patch("custom_components.marketplace_refresh.add_extra_js_url") as add_js:
        await _setup(hass)
        await hass.async_block_till_done()
    add_js.assert_called_once()


def _marketplace_update_entities(hass: HomeAssistant, states: dict[str, str]) -> None:
    """Marketplace update entities in the registry, with these states."""
    registry = er.async_get(hass)
    for object_id, state in states.items():
        registry.async_get_or_create("update", "marketplace", object_id, suggested_object_id=object_id)
        hass.states.async_set(f"update.{object_id}", state, {"title": object_id.replace("_", " ").title()})


def _fake_update_install(hass: HomeAssistant, fail: set[str] | None = None) -> list[str]:
    """update.install stand-in: turns the entity off, or fails for the ones in `fail`. Returns the calls, in order."""
    calls: list[str] = []

    async def install(call) -> None:
        for entity_id in cv.entity_ids(call.data["entity_id"]):
            calls.append(entity_id)
            await asyncio.sleep(0)
            if entity_id in (fail or set()):
                raise HomeAssistantError("download failed")
            hass.states.async_set(entity_id, "off", hass.states.get(entity_id).attributes)

    hass.services.async_register("update", "install", install)
    return calls


async def test_install_updates_installs_every_update_one_by_one(hass, fake_marketplace):
    await _setup(hass)
    _marketplace_update_entities(hass, {"mushroom": "on", "card_mod": "on", "parcel": "off"})
    calls = _fake_update_install(hass)
    await hass.services.async_call(DOMAIN, "install_updates", {"wait": True}, blocking=True)
    await hass.async_block_till_done()
    assert calls == ["update.card_mod", "update.mushroom"]
    state = hass.states.get(STATUS)
    assert state.attributes["installing"] == []
    assert state.attributes["install_failed"] == []
    assert hass.states.get(BUTTON).state != "unavailable"


async def test_install_updates_only_the_entities_given(hass, fake_marketplace):
    await _setup(hass)
    _marketplace_update_entities(hass, {"mushroom": "on", "card_mod": "on"})
    calls = _fake_update_install(hass)
    await hass.services.async_call(
        DOMAIN, "install_updates", {"entity_id": "update.mushroom", "wait": True}, blocking=True
    )
    assert calls == ["update.mushroom"]


async def test_install_updates_reports_failures_and_goes_on(hass, fake_marketplace):
    await _setup(hass)
    _marketplace_update_entities(hass, {"mushroom": "on", "card_mod": "on"})
    calls = _fake_update_install(hass, fail={"update.card_mod"})
    with pytest.raises(HomeAssistantError, match="Card Mod: download failed"):
        await hass.services.async_call(DOMAIN, "install_updates", {"wait": True}, blocking=True)
    assert calls == ["update.card_mod", "update.mushroom"]
    assert hass.states.get(STATUS).attributes["install_failed"] == ["Card Mod: download failed"]


async def test_install_updates_progress_and_no_second_run(hass, fake_marketplace):
    await _setup(hass)
    _marketplace_update_entities(hass, {"mushroom": "on", "card_mod": "on"})
    release = asyncio.Event()

    async def install(call) -> None:
        await release.wait()
        hass.states.async_set(call.data["entity_id"], "off")

    hass.services.async_register("update", "install", install)
    await hass.services.async_call(DOMAIN, "install_updates", {}, blocking=True)
    await hass.async_block_till_done(wait_background_tasks=False)
    assert hass.states.get(STATUS).attributes["installing"] == ["update.card_mod", "update.mushroom"]
    assert hass.states.get(BUTTON).state == "unavailable"
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "install_updates", {}, blocking=True)
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(STATUS).attributes["installing"] == []


async def test_install_updates_rejects_other_entities(hass, fake_marketplace):
    await _setup(hass)
    hass.states.async_set("update.core", "on")
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "install_updates", {"entity_id": "update.core"}, blocking=True)


async def test_install_updates_admin_only(hass, fake_marketplace, hass_read_only_user):
    from homeassistant.exceptions import Unauthorized

    await _setup(hass)
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN, "install_updates", {}, blocking=True, context=Context(user_id=hass_read_only_user.id)
        )


async def _blocked_install(hass: HomeAssistant) -> asyncio.Event:
    """Start install_updates on two Marketplace updates whose install waits for the event returned."""
    _marketplace_update_entities(hass, {"mushroom": "on", "card_mod": "on"})
    release = asyncio.Event()

    async def install(call) -> None:
        await release.wait()
        hass.states.async_set(call.data["entity_id"], "off")

    hass.services.async_register("update", "install", install)
    await hass.services.async_call(DOMAIN, "install_updates", {}, blocking=True)
    await hass.async_block_till_done(wait_background_tasks=False)
    assert hass.states.get(STATUS).attributes["installing"] == ["update.card_mod", "update.mushroom"]
    return release


async def test_check_updates_refused_while_installing(hass, fake_marketplace):
    """check_updates doesn't start a full check (refreshing the repositories being downloaded) during installs."""
    await _setup(hass)
    release = await _blocked_install(hass)
    with pytest.raises(ServiceValidationError, match="being installed"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)
    assert hass.states.get(STATUS).state == "idle"
    assert hass.states.get(STATUS).attributes["installing"] == ["update.card_mod", "update.mushroom"]
    fake_marketplace.repositories.list_installed[0].update_repository.assert_not_awaited()
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    # Once the installs are done, a check starts again.
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    fake_marketplace.repositories.list_installed[0].update_repository.assert_awaited_once()


async def test_scheduled_check_due_during_installs_runs_after_them(hass, fake_marketplace, freezer):
    """A scheduled check due while updates are installed runs once they are done, not during them."""
    entry = await _setup(hass, hours=2)
    repo = fake_marketplace.repositories.list_installed[0]
    release = await _blocked_install(hass)
    freezer.tick(timedelta(hours=2, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=False)
    assert hass.states.get(STATUS).state == "idle"
    repo.update_repository.assert_not_awaited()
    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    repo.update_repository.assert_awaited_once()
    # And the next one is scheduled an interval later as usual.
    freezer.tick(timedelta(hours=2, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    assert repo.update_repository.await_count == 2


async def test_unload_during_installs_leaves_no_scheduled_check(hass, fake_marketplace, freezer):
    """Unloading while installing cancels the installs without scheduling a check on the unloaded entry."""
    entry = await _setup(hass, hours=2)
    repo = fake_marketplace.repositories.list_installed[0]
    await _blocked_install(hass)
    freezer.tick(timedelta(hours=2, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=False)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(timedelta(hours=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
