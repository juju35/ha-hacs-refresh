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
from collections.abc import Callable
from datetime import datetime
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import HACS_DOMAIN, PARALLEL_REFRESHES, STATE_ERROR, STATE_IDLE, STATE_RUNNING

_LOGGER = logging.getLogger(__name__)


class HacsNotAvailableError(HomeAssistantError):
    """HACS is not loaded, disabled, or its internals changed."""


def _hacs(hass: HomeAssistant) -> Any:
    hacs = hass.data.get(HACS_DOMAIN)
    if hacs is None:
        raise HacsNotAvailableError("HACS is not loaded")
    for path in ("repositories.list_downloaded", "data.async_write", "coordinators", "system.disabled"):
        obj = hacs
        for attr in path.split("."):
            if not hasattr(obj, attr):
                raise HacsNotAvailableError(
                    f"This version of HACS is not supported (missing {path}); "
                    "please open an issue on https://github.com/juju35/ha-hacs-refresh"
                )
            obj = getattr(obj, attr)
    if hacs.system.disabled:
        raise HacsNotAvailableError(f"HACS is disabled ({hacs.system.disabled_reason})")
    return hacs


class HacsRefresher:
    """Runs the check and keeps its progress for the button and the sensor."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.state: str = STATE_IDLE
        self.done = 0
        self.total = 0
        self.updates: int | None = None
        self.failed: list[str] = []
        self.error: str | None = None
        self.last_check: datetime | None = None
        self._task: asyncio.Task | None = None
        self._listeners: list[CALLBACK_TYPE] = []

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
        self._task = self.hass.async_create_background_task(self._async_run(), "hacs_refresh_check")
        return True

    async def async_wait(self) -> None:
        """Wait for the running check, if any."""
        if self._task is not None:
            await asyncio.shield(self._task)

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
            _LOGGER.error("HACS check failed: %s", err)
            self.error = str(err)
            self.state = STATE_ERROR
        self.last_check = dt_util.utcnow()
        self._task = None
        self._notify()
