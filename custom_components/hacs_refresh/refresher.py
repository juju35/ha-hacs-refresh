"""Check every repository downloaded with HACS for updates, on the server.

HACS has no action to do this: it refreshes downloaded custom repositories every 48 hours,
and its frontend refreshes one repository at a time over its websocket API. This module does
for every downloaded repository what HACS' `hacs/repository/refresh` command does for one:

    await repository.update_repository(ignore_issues=True, force=True)
    await hacs.data.async_write()
    hacs.coordinators[category].async_update_listeners()

It only touches these attributes of HACS' internal object (`hass.data["hacs"]`), and checks
they exist so a future HACS version fails with a clear message instead of a crash.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, HACS_DOMAIN, PARALLEL_REFRESHES, STATE_ERROR, STATE_IDLE, STATE_RUNNING

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
ISSUES_URL = "https://github.com/juju35/ha-hacs-refresh/issues"


class HacsNotAvailableError(HomeAssistantError):
    """HACS is not loaded, disabled, or its internals changed."""

    def __init__(self, translation_key: str, placeholders: dict[str, str] | None = None) -> None:
        super().__init__(
            translation_domain=DOMAIN, translation_key=translation_key, translation_placeholders=placeholders
        )


def _hacs(hass: HomeAssistant) -> Any:
    hacs = hass.data.get(HACS_DOMAIN)
    if hacs is None:
        raise HacsNotAvailableError("hacs_not_loaded")
    for path in (
        "repositories.list_downloaded",
        "data.async_write",
        "coordinators",
        "system.disabled",
    ):
        obj = hacs
        for attr in path.split("."):
            if not hasattr(obj, attr):
                raise HacsNotAvailableError("hacs_not_supported", {"path": path, "issues": ISSUES_URL})
            obj = getattr(obj, attr)
    if hacs.system.disabled:
        raise HacsNotAvailableError("hacs_disabled", {"reason": str(getattr(hacs.system, "disabled_reason", None))})
    return hacs


def _raise_failed(failed: list[str]) -> None:
    if failed:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="check_failed",
            translation_placeholders={"failed": "; ".join(failed)},
        )


def _cancelling() -> bool:
    """Whether the running task is being cancelled itself (not just something it waits for)."""
    current = asyncio.current_task()
    return current is not None and bool(current.cancelling())


def _parse(value: Any) -> datetime | None:
    return dt_util.parse_datetime(value) if isinstance(value, str) else None


class HacsRefresher:
    """Runs the check and keeps its progress for the button and the sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        # The last full check and its result, kept across restarts for the interval and the sensors.
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, DOMAIN)
        # Called when a full check ends, whatever started it.
        self.on_done: CALLBACK_TYPE | None = None
        self.state: str = STATE_IDLE
        self.done = 0
        self.total = 0
        self.updates: int | None = None
        self.failed: list[str] = []
        self.error: str | None = None
        self.last_check: datetime | None = None
        self.since: datetime | None = None
        # Update entities of the repositories checked on their own (check_repository).
        self.checking: set[str] = set()
        # Repositories being checked on their own, by repository id: resolved with the error (or None) once checked,
        # so that another call or the full check waits for that result instead of refreshing them a second time.
        self._single: dict[str, asyncio.Future[str | None]] = {}
        self._task: asyncio.Task | None = None
        self._listeners: list[CALLBACK_TYPE] = []

    async def async_load(self) -> None:
        """Restore the last check from the previous run."""
        data = await self._store.async_load() or {}
        self.last_check = _parse(data.get("last_check"))
        self.updates = data.get("updates")
        # Before the first check, the interval counts from the first setup.
        self.since = _parse(data.get("since"))
        if self.since is None:
            self.since = dt_util.utcnow()
            await self._async_save()

    async def _async_save(self) -> None:
        await self._store.async_save(
            {
                "since": self.since.isoformat() if self.since else None,
                "last_check": self.last_check.isoformat() if self.last_check else None,
                "updates": self.updates,
            }
        )

    @property
    def running(self) -> bool:
        return self.state == STATE_RUNNING

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> Callable[[], None]:
        """Entities listen to progress changes."""
        self._listeners.append(update_callback)
        return lambda: self._listeners.remove(update_callback)

    @callback
    def _notify(self) -> None:
        for update_callback in list(self._listeners):
            update_callback()

    @callback
    def async_start(self) -> bool:
        """Start a check in the background. Returns False when one is already running."""
        if self.running:
            return False
        _hacs(self.hass)  # fail now, in the caller, if HACS can't be used
        self.state = STATE_RUNNING
        self.done = 0
        self.total = 0
        self.failed = []
        self.error = None
        self._notify()
        # Tied to the entry: unloading it (options changed, removed) cancels a check still running.
        self._task = self.entry.async_create_background_task(self.hass, self._async_run(), "hacs_refresh_check")
        return True

    async def async_check_repositories(self, entity_ids: list[str]) -> None:
        """Check the repositories behind these HACS update entities, and wait for the result.

        Independent of the full check: it neither changes the status nor the last check,
        the entities being checked are listed in the status sensor's `checking` attribute.
        While a full check runs, it waits for its end and reports its result for these repositories;
        a repository already being checked by another call is not checked a second time: this call
        waits for that result.
        """
        hacs = _hacs(self.hass)
        registry = er.async_get(self.hass)
        by_id = {str(repo.data.id): repo for repo in hacs.repositories.list_downloaded}
        targets: dict[str, Any] = {}
        for entity_id in entity_ids:
            entry = registry.async_get(entity_id)
            if entry is None or entry.platform != HACS_DOMAIN or entry.domain != "update":
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="not_hacs_update_entity",
                    translation_placeholders={"entity_id": entity_id},
                )
            repo = by_id.get(str(entry.unique_id))
            if repo is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="not_downloaded",
                    translation_placeholders={"entity_id": entity_id},
                )
            targets[entity_id] = repo
        if self.running:
            # The full check refreshes these repositories too: wait for its end instead of a second refresh.
            await self.async_wait()
            if self.state == STATE_ERROR:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="full_check_failed",
                    translation_placeholders={"error": str(self.error)},
                )
            _raise_failed([repo.data.full_name for repo in targets.values() if repo.data.full_name in self.failed])
            return
        # Already being checked by another call: wait for that result.
        waiting: dict[str, asyncio.Future[str | None]] = {}
        own: dict[str, Any] = {}
        own_keys: set[str] = set()
        for entity_id, repo in targets.items():
            key = str(repo.data.id)
            if key in self._single:
                waiting[key] = self._single[key]
            elif key not in own_keys:
                own_keys.add(key)
                own[entity_id] = repo
        futures = {str(repo.data.id): self.hass.loop.create_future() for repo in own.values()}
        self._single.update(futures)
        self.checking.update(own)
        if own:
            self._notify()
        failed: list[str] = []
        try:
            for repo in own.values():
                error: str | None = None
                try:
                    await repo.update_repository(ignore_issues=True, force=True)
                except Exception as err:  # noqa: BLE001 - report every failure at the end
                    _LOGGER.warning("Could not check %s: %s", repo.data.full_name, err)
                    error = f"{repo.data.full_name}: {err}"
                    failed.append(error)
                futures[str(repo.data.id)].set_result(error)
            if own:
                await hacs.data.async_write()
                for category in {repo.data.category for repo in own.values()}:
                    if coordinator := hacs.coordinators.get(category):
                        coordinator.async_update_listeners()
        finally:
            for key, fut in futures.items():
                # Interrupted before this repository was checked: whoever waits for it checks it or fails.
                if not fut.done():
                    fut.cancel()
                if self._single.get(key) is fut:
                    del self._single[key]
            self.checking.difference_update(own)
            if own:
                self._notify()
        for fut in waiting.values():
            try:
                error = await asyncio.shield(fut)
            except asyncio.CancelledError:
                if not fut.cancelled() or _cancelling():
                    raise
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="check_cancelled") from None
            if error:
                failed.append(error)
        _raise_failed(failed)

    async def async_wait(self) -> None:
        """Wait for the running check, if any.

        Unloading the entry cancels the check: a caller that was not cancelled itself gets an error
        instead of the check's CancelledError.
        """
        task = self._task
        if task is None:
            return
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.cancelled() and not _cancelling():
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="check_cancelled") from None
            raise

    async def _async_run(self) -> None:
        try:
            hacs = _hacs(self.hass)
            categories = getattr(getattr(hacs, "common", None), "categories", None)
            repositories = [
                repo
                for repo in hacs.repositories.list_downloaded
                if categories is None or repo.data.category in categories
            ]
            self.total = len(repositories)
            self._notify()
            _LOGGER.info("Checking %s HACS repositories for updates", self.total)

            semaphore = asyncio.Semaphore(PARALLEL_REFRESHES)

            async def refresh(repo: Any) -> None:
                # Being checked by check_repository: take that result instead of refreshing it a second time.
                if (single := self._single.get(str(repo.data.id))) is not None:
                    try:
                        if await asyncio.shield(single):
                            self.failed.append(repo.data.full_name)
                        self.done += 1
                        self._notify()
                        return
                    except asyncio.CancelledError:
                        # That call was interrupted before checking it: check it here, unless this check is
                        # being cancelled too.
                        if not single.cancelled() or _cancelling():
                            raise
                async with semaphore:
                    try:
                        await repo.update_repository(ignore_issues=True, force=True)
                    except Exception as err:  # noqa: BLE001 - one repository must not stop the others
                        _LOGGER.warning("Could not check %s: %s", repo.data.full_name, err)
                        self.failed.append(repo.data.full_name)
                    self.done += 1
                    self._notify()

            await asyncio.gather(*(refresh(repo) for repo in repositories))
            await hacs.data.async_write()
            # The update entities only change when their coordinator says so.
            for coordinator in hacs.coordinators.values():
                coordinator.async_update_listeners()
            self.updates = sum(1 for repo in repositories if getattr(repo, "pending_update", False))
            self.state = STATE_IDLE
            _LOGGER.info(
                "HACS check done: %s update(s) available, %s repository(ies) failed",
                self.updates,
                len(self.failed),
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("HACS check failed")
            self.error = str(err)
            self.state = STATE_ERROR
        self.last_check = dt_util.utcnow()
        self._task = None
        self._notify()
        await self._async_save()
        if self.on_done is not None:
            self.on_done()
