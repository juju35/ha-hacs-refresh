"""Tests for HACS Refresh."""

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
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.hacs_refresh.const import CARD_URL, CONF_SCAN_INTERVAL, DOMAIN

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


async def test_overdue_check_runs_at_startup(hass, fake_hacs, hass_storage):
    """A restart doesn't postpone the automatic check: an overdue one runs once Home Assistant has started."""
    last = dt_util.utcnow() - timedelta(hours=25)
    hass_storage[DOMAIN] = {"version": 1, "key": DOMAIN, "data": {"last_check": last.isoformat(), "updates": 2}}
    entry = await _setup(hass)
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    fake_hacs.repositories.list_downloaded[0].update_repository.assert_awaited_once()
    assert hass_storage[DOMAIN]["data"]["updates"] == 1
    assert dt_util.parse_datetime(hass_storage[DOMAIN]["data"]["last_check"]) > last


async def test_recent_check_is_restored_and_next_one_kept(hass, fake_hacs, hass_storage, freezer):
    last = dt_util.utcnow() - timedelta(hours=20)
    hass_storage[DOMAIN] = {"version": 1, "key": DOMAIN, "data": {"last_check": last.isoformat(), "updates": 2}}
    entry = await _setup(hass)
    repo = fake_hacs.repositories.list_downloaded[0]
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


async def test_first_install_waits_one_interval(hass, fake_hacs, hass_storage, freezer):
    entry = await _setup(hass, hours=2)
    repo = fake_hacs.repositories.list_downloaded[0]
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


async def test_unload_cancels_running_check(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_hacs.repositories.list_downloaded[0].update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    old = entry.runtime_data
    assert old.async_start()
    await hass.async_block_till_done()
    assert old.running
    task = old._task
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert task.cancelled()
    fake_hacs.data.async_write.assert_not_awaited()
    release.set()


async def test_check_updates_open_to_non_admin(hass, fake_hacs, hass_read_only_user):
    """Like the button, which runs the same check, the action is open to every user."""
    await _setup(hass, hours=0)
    await hass.services.async_call(
        DOMAIN, "check_updates", {"wait": True}, blocking=True, context=Context(user_id=hass_read_only_user.id)
    )
    fake_hacs.repositories.list_downloaded[0].update_repository.assert_awaited_once()


async def test_hacs_disabled_without_reason(hass, fake_hacs):
    """A HACS version without disabled_reason still gives the clear error."""
    await _setup(hass)
    fake_hacs.system.disabled = True
    del fake_hacs.system.disabled_reason
    with pytest.raises(ServiceValidationError, match="HACS is disabled"):
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_check_repository_waits_for_full_check(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_check_repository_skips_entity_already_checking(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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
    fake_hacs.data.async_write.assert_awaited_once()


async def _await_service(call: asyncio.Task) -> None:
    """Await a service call task; a raw CancelledError (the caller was not cancelled) fails the test."""
    try:
        async with asyncio.timeout(5):
            await call
    except asyncio.CancelledError:
        pytest.fail("the action ended with a raw CancelledError")


async def test_waiting_check_updates_fails_cleanly_on_unload(hass, fake_hacs):
    """Unloading the entry cancels the check: an action waiting for it gets a Home Assistant error."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_hacs.repositories.list_downloaded[0].update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    call = hass.async_create_task(hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True))
    await asyncio.sleep(0.01)
    assert not call.done()
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(HomeAssistantError, match="cancelled"):
        await _await_service(call)
    release.set()


async def test_waiting_check_repository_fails_cleanly_on_unload(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_full_check_waits_for_running_check_repository(hass, fake_hacs):
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

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_full_check_reports_failure_of_awaited_check_repository(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_second_check_repository_waits_for_the_first(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_check_repository_during_failing_full_check(hass, fake_hacs):
    """check_repository waiting for a full check fails when that check couldn't check its repository."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()
        raise RuntimeError("GitHub down")

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
    other = _hacs_update_entity(hass, fake_hacs.repositories.list_downloaded[0])
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


async def test_check_repository_during_full_check_in_error(hass, fake_hacs):
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    fake_hacs.data.async_write.side_effect = OSError("disk full")
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_check_repository_calls_cancelled_together(hass, fake_hacs):
    """Two check_repository calls on one repository, cancelled in the same tick, both get CancelledError."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_full_check_cancelled_with_awaited_check_repository(hass, fake_hacs):
    """A full check cancelled together with the check_repository it waits for stops, without refreshing again."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_check_repository_checks_itself_when_the_awaited_call_is_cancelled(hass, fake_hacs):
    """A check_repository waiting for another call's result checks the repository itself if that call is cancelled."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_waiting_check_repository_sees_the_write_failure(hass, fake_hacs):
    """A check_repository waiting for another call must not report success when the HACS data write fails."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    parcel = fake_hacs.repositories.list_downloaded[1]
    parcel.update_repository.side_effect = slow
    fake_hacs.data.async_write.side_effect = OSError("disk full")
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, parcel)
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


async def test_check_updates_wait_fails_on_failed_repository(hass, fake_hacs):
    """With wait: true, the action fails like check_repository when a repository could not be checked."""
    fake_hacs.repositories.list_downloaded.append(make_repo("someone/broken", fail=True))
    await _setup(hass, hours=0)
    with pytest.raises(HomeAssistantError, match="someone/broken"):
        await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    # Without wait, the action only starts the check.
    await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)


async def test_check_updates_wait_fails_when_full_check_fails(hass, fake_hacs):
    fake_hacs.data.async_write.side_effect = OSError("disk full")
    await _setup(hass, hours=0)
    with pytest.raises(HomeAssistantError, match="disk full"):
        await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=True)
    assert hass.states.get(STATUS).state == "error"


async def test_failed_attribute_is_a_copy(hass, fake_hacs):
    """The published `failed` attribute is not the list the running check appends to."""
    fake_hacs.repositories.list_downloaded.append(make_repo("someone/broken", fail=True))
    entry = await _setup(hass, hours=0)
    await hass.services.async_call(DOMAIN, "check_updates", {"wait": True}, blocking=False)
    await entry.runtime_data.async_wait()
    await hass.async_block_till_done()
    failed = hass.states.get(STATUS).attributes["failed"]
    assert failed == ["someone/broken"]
    assert failed is not entry.runtime_data.failed


async def test_skipped_scheduled_check_retried_within_the_hour(hass, fake_hacs, freezer):
    """A scheduled check skipped because HACS is disabled is tried again after an hour, not a full interval."""
    entry = await _setup(hass, hours=24)
    repo = fake_hacs.repositories.list_downloaded[0]
    fake_hacs.system.disabled = True
    fake_hacs.system.disabled_reason = "rate_limit"
    freezer.tick(timedelta(hours=24, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    fake_hacs.system.disabled = False
    freezer.tick(timedelta(minutes=59))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    repo.update_repository.assert_not_awaited()
    freezer.tick(timedelta(minutes=1, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await entry.runtime_data.async_wait()
    repo.update_repository.assert_awaited_once()


async def test_hacs_disabled_without_reason_has_no_placeholder(hass, fake_hacs):
    await _setup(hass)
    fake_hacs.system.disabled = True
    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(DOMAIN, "check_updates", {}, blocking=True)
    assert err.value.translation_key == "hacs_disabled_unknown"
    assert "unknown" not in str(err.value)


async def test_check_repository_during_full_check_outside_its_categories(hass, fake_hacs):
    """A repository whose category the full check leaves out is checked by check_repository itself."""
    release = asyncio.Event()

    async def slow(**_kwargs):
        await release.wait()

    fake_hacs.repositories.list_downloaded[1].update_repository.side_effect = slow
    script = make_repo("someone/script", category="python_script")
    fake_hacs.repositories.list_downloaded.append(script)
    entry = await _setup(hass, hours=0)
    entity_id = _hacs_update_entity(hass, script)
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


async def test_next_check_for_the_card(hass, fake_hacs):
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


async def test_next_check_when_automatic_check_is_off(hass, fake_hacs):
    await _setup(hass, hours=0)
    attrs = hass.states.get(LAST_CHECK).attributes
    assert attrs["scan_interval"] == 0
    assert attrs["next_check"] is None


async def test_card_is_served(hass, fake_hacs, hass_client):
    await _setup(hass)
    client = await hass_client()
    response = await client.get(CARD_URL)
    assert response.status == 200
    assert "hacs-refresh-card" in await response.text()


async def test_card_resource_back_after_remove_and_add(hass, fake_hacs):
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
async def test_card_resource_with_lovelace_data_variants(hass, fake_hacs, key: str, container: type):
    """hass.data["lovelace"]: a dict before 2025.2, then a dataclass with `mode`, renamed `resource_mode` in 2026.2."""
    assert await async_setup_component(hass, "lovelace", {})
    resources = _resources(hass)
    hass.data["lovelace"] = container(**{key: "storage", "resources": resources, "dashboards": {}})
    entry = await _setup(hass)
    assert len(_card_urls(resources)) == 1
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert _card_urls(resources) == []


async def test_card_resource_yaml_mode_untouched(hass, fake_hacs):
    """Resources in YAML mode are not edited (the card is loaded on every page instead)."""
    from homeassistant.components.lovelace.resources import ResourceYAMLCollection

    assert await async_setup_component(hass, "lovelace", {})
    hass.data["lovelace"] = {"mode": "yaml", "resources": ResourceYAMLCollection([]), "dashboards": {}}
    with patch("custom_components.hacs_refresh.add_extra_js_url") as add_js:
        await _setup(hass)
        await hass.async_block_till_done()
    add_js.assert_called_once()
