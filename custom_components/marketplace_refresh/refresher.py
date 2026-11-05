"""Check every repository installed from the Marketplace for updates, on the server.

The Marketplace has no action to do this: it reads the catalog every 6 hours, refreshes the
installed custom repositories from GitHub every 48 hours (with a connected GitHub account),
and its panel refreshes one repository at a time over its websocket API. A full check here:

1. reads the catalog again (`async_get_all_category_repositories`): one request per category,
   no GitHub API call, it carries the latest version of every catalog repository;
2. with a GitHub account connected, does for every installed repository what the
   `marketplace/repository/refresh` command does for one:

       await repository.update_repository(ignore_issues=True, force=True)
       await marketplace.data.async_write()
       marketplace.coordinators[category].async_update_listeners()

   Without a connection the Marketplace is on GitHub's anonymous limit (60 requests an hour),
   far too small for that: the catalog is the only source then, and the custom repositories,
   which the catalog doesn't list, are reported as not checked.

It only touches these attributes of the Marketplace manager (`runtime_data` of its config
entry), and checks they exist so a future Home Assistant version fails with a clear message
instead of a crash.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON
from homeassistant.core import CALLBACK_TYPE, Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MARKETPLACE_DOMAIN, PARALLEL_REFRESHES, STATE_ERROR, STATE_IDLE, STATE_RUNNING

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
ISSUES_URL = "https://github.com/juju35/ha-marketplace-refresh/issues"
# Least time between two progress notifications during the full check: without it, a large
# installation (100+ repositories) writes hundreds of states (and recorder rows) in a few seconds.
PROGRESS_INTERVAL = 0.5


class MarketplaceNotAvailableError(HomeAssistantError):
    """The Marketplace is not loaded, disabled, or its internals changed."""

    def __init__(self, translation_key: str, placeholders: dict[str, str] | None = None) -> None:
        super().__init__(
            translation_domain=DOMAIN, translation_key=translation_key, translation_placeholders=placeholders
        )


def _loaded_marketplace(hass: HomeAssistant) -> Any | None:
    """The Marketplace manager, from its loaded config entry (the manifest allows a single one), else None."""
    entries = hass.config_entries.async_loaded_entries(MARKETPLACE_DOMAIN)
    return getattr(entries[0], "runtime_data", None) if entries else None


def _marketplace(hass: HomeAssistant) -> Any:
    """The Marketplace manager, checked to be usable."""
    marketplace = _loaded_marketplace(hass)
    if marketplace is None:
        raise MarketplaceNotAvailableError("marketplace_not_loaded")
    for path in (
        "repositories.list_installed",
        "repositories.is_default",
        "data.async_write",
        "coordinators",
        "system.disabled",
        "github_connected",
        "async_get_all_category_repositories",
    ):
        obj = marketplace
        for attr in path.split("."):
            if not hasattr(obj, attr):
                raise MarketplaceNotAvailableError("marketplace_not_supported", {"path": path, "issues": ISSUES_URL})
            obj = getattr(obj, attr)
    if marketplace.system.disabled:
        reason = getattr(marketplace.system, "disabled_reason", None)
        if reason is None:
            raise MarketplaceNotAvailableError("marketplace_disabled_unknown")
        raise MarketplaceNotAvailableError("marketplace_disabled", {"reason": str(reason)})
    return marketplace


def _in_full_check(marketplace: Any, repo: Any) -> bool:
    """Whether the full check refreshes this repository (the Marketplace's own categories, when it lists them)."""
    categories = getattr(getattr(marketplace, "common", None), "categories", None)
    return categories is None or repo.data.category in categories


def _custom(marketplace: Any, repo: Any) -> bool:
    """Whether the repository was added from a link: the catalog doesn't list it, only GitHub can check it."""
    return not marketplace.repositories.is_default(repo.data.id)


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


class MarketplaceRefresher:
    """Runs the check and keeps its progress for the button and the sensor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        # The last full check and its result, kept across restarts for the interval and the sensors.
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, DOMAIN)
        # Called when a full check ends, whatever started it.
        self.on_done: CALLBACK_TYPE | None = None
        # Called when the installs end (not when they are cancelled by an unload).
        self.on_install_done: CALLBACK_TYPE | None = None
        self.state: str = STATE_IDLE
        self.done = 0
        self.total = 0
        self.updates: int | None = None
        self.failed: list[str] = []
        self.error: str | None = None
        self.last_check: datetime | None = None
        self.since: datetime | None = None
        # Whether a GitHub account was connected to the Marketplace at the last check: without one,
        # only the catalog is read, and the repositories added from a link can't be checked.
        self.github_connected: bool | None = None
        # Update entities of the repositories checked on their own (check_repository).
        self.checking: set[str] = set()
        # Repositories being checked on their own, by repository id: resolved with the error (or None) once checked,
        # so that another call or the full check waits for that result instead of refreshing them a second time.
        self._single: dict[str, asyncio.Future[str | None]] = {}
        self._task: asyncio.Task | None = None
        # Update entities left to install (the one being installed first), and the ones that failed ("title: error").
        self.installing: list[str] = []
        self.install_failed: list[str] = []
        self._install_task: asyncio.Task | None = None
        self._listeners: list[CALLBACK_TYPE] = []
        # When the entities were last notified of the full check's progress (loop time).
        self._progress_at = 0.0

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

    @property
    def installing_updates(self) -> bool:
        return self._install_task is not None

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
    def _notify_progress(self) -> None:
        """Notify the progress of the full check, at most every PROGRESS_INTERVAL seconds.

        The next repository checked after the interval notifies, and the end of the check
        always notifies (`_notify` in `_async_run`), so the final state is never skipped.
        """
        now = self.hass.loop.time()
        if now - self._progress_at < PROGRESS_INTERVAL:
            return
        self._progress_at = now
        self._notify()

    @callback
    def async_start(self) -> bool:
        """Start a check in the background. Returns False when one is already running.

        Refused while updates are installed: the check would refresh the repositories being downloaded.
        """
        if self.running:
            return False
        if self.installing_updates:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="check_while_installing")
        _marketplace(self.hass)  # fail now, in the caller, if the Marketplace can't be used
        self.state = STATE_RUNNING
        self.done = 0
        self.total = 0
        self.failed = []
        self.error = None
        self._progress_at = 0.0
        self._notify()
        # Tied to the entry: unloading it (options changed, removed) cancels a check still running.
        self._task = self.entry.async_create_background_task(self.hass, self._async_run(), "marketplace_refresh_check")
        return True

    async def async_check_repositories(self, entity_ids: list[str]) -> None:
        """Check the repositories behind these Marketplace update entities, and wait for the result.

        Independent of the full check: it neither changes the status nor the last check,
        the entities being checked are listed in the status sensor's `checking` attribute.
        While a full check runs, it waits for its end and reports its result for these repositories;
        a repository already being checked by another call is not checked a second time: this call
        waits for that result, and checks it itself if that call is cancelled first.
        """
        marketplace = _marketplace(self.hass)
        registry = er.async_get(self.hass)
        by_id = {str(repo.data.id): repo for repo in marketplace.repositories.list_installed}
        targets: dict[str, Any] = {}
        for entity_id in entity_ids:
            entry = registry.async_get(entity_id)
            if entry is None or entry.platform != MARKETPLACE_DOMAIN or entry.domain != "update":
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="not_marketplace_update_entity",
                    translation_placeholders={"entity_id": entity_id},
                )
            repo = by_id.get(str(entry.unique_id))
            if repo is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="not_installed",
                    translation_placeholders={"entity_id": entity_id},
                )
            targets[entity_id] = repo
        _raise_failed(await self._async_check_targets(targets))

    async def _async_check_targets(self, targets: dict[str, Any]) -> list[str]:
        """Check these repositories (entity id → repository) and return the failures."""
        marketplace = _marketplace(self.hass)
        if self.running:
            # The full check refreshes these repositories too: wait for its end instead of a second refresh.
            # A repository whose category it leaves out is checked here once it ends.
            covered = {e: repo for e, repo in targets.items() if _in_full_check(marketplace, repo)}
            left_out = {e: repo for e, repo in targets.items() if e not in covered}
            await self.async_wait()
            failed: list[str] = []
            if covered:
                self.raise_if_full_check_failed()
                failed = [repo.data.full_name for repo in covered.values() if repo.data.full_name in self.failed]
            if left_out:
                failed.extend(await self._async_check_targets(left_out))
            return failed
        # Already being checked by another call: wait for that result.
        waiting: dict[str, tuple[asyncio.Future[str | None], str, Any]] = {}
        own: dict[str, Any] = {}
        own_keys: set[str] = set()
        for entity_id, repo in targets.items():
            key = str(repo.data.id)
            if key in self._single:
                waiting[key] = (self._single[key], entity_id, repo)
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
            errors: dict[str, str | None] = {}
            for repo in own.values():
                error: str | None = None
                try:
                    await repo.update_repository(ignore_issues=True, force=True)
                except Exception as err:  # noqa: BLE001 - report every failure at the end
                    _LOGGER.warning("Could not check %s: %s", repo.data.full_name, err)
                    error = f"{repo.data.full_name}: {err}"
                    failed.append(error)
                errors[str(repo.data.id)] = error
            if own:
                await marketplace.data.async_write()
                for category in {repo.data.category for repo in own.values()}:
                    if coordinator := marketplace.coordinators.get(category):
                        coordinator.async_update_listeners()
            # Only resolved once the Marketplace data is written and the coordinators notified: if the write
            # fails, the futures are cancelled below and whoever waits for them checks again or fails.
            for key, error in errors.items():
                futures[key].set_result(error)
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
        retry: dict[str, Any] = {}
        for fut, entity_id, repo in waiting.values():
            try:
                error = await asyncio.shield(fut)
            except asyncio.CancelledError:
                if not fut.cancelled() or _cancelling():
                    raise
                # That call was interrupted before checking it: check it here, like the full check does.
                retry[entity_id] = repo
                continue
            if error:
                failed.append(error)
        if retry:
            failed.extend(await self._async_check_targets(retry))
        return failed

    def raise_if_full_check_failed(self) -> None:
        """Raise when the last full check failed."""
        if self.state == STATE_ERROR:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="full_check_failed",
                translation_placeholders={"error": str(self.error)},
            )

    def raise_for_result(self) -> None:
        """Raise when the last full check failed or could not check some repositories."""
        self.raise_if_full_check_failed()
        _raise_failed(self.failed)

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

    def _installable(self, entity_ids: list[str] | None) -> list[str]:
        """These Marketplace update entities, else all, keeping the ones with an update that isn't being installed."""
        registry = er.async_get(self.hass)
        if entity_ids is None:
            candidates = sorted(
                e.entity_id
                for e in registry.entities.values()
                if e.platform == MARKETPLACE_DOMAIN and e.domain == "update"
            )
        else:
            candidates = []
            for entity_id in dict.fromkeys(entity_ids):
                entry = registry.async_get(entity_id)
                if entry is None or entry.platform != MARKETPLACE_DOMAIN or entry.domain != "update":
                    raise ServiceValidationError(
                        translation_domain=DOMAIN,
                        translation_key="not_marketplace_update_entity",
                        translation_placeholders={"entity_id": entity_id},
                    )
                candidates.append(entity_id)
        return [
            entity_id
            for entity_id in candidates
            if (state := self.hass.states.get(entity_id)) is not None
            and state.state == STATE_ON
            and not state.attributes.get("in_progress")
        ]

    @callback
    def async_start_install(self, entity_ids: list[str] | None, context: Context | None) -> None:
        """Install the updates of these Marketplace update entities (else all), one by one, in the background."""
        if self.installing_updates:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="install_running")
        _marketplace(self.hass)  # fail now, in the caller, if the Marketplace can't be used
        self.installing = self._installable(entity_ids)
        self.install_failed = []
        # Tied to the entry, like the check: unloading it cancels the installs left.
        self._install_task = self.entry.async_create_background_task(
            self.hass, self._async_install(context), "marketplace_refresh_install"
        )
        self._notify()  # once the task is set: the button greys out

    async def async_wait_install(self) -> None:
        """Wait for the installs running, then fail if some could not be installed."""
        task = self._install_task
        if task is not None:
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                if task.cancelled() and not _cancelling():
                    raise HomeAssistantError(translation_domain=DOMAIN, translation_key="install_cancelled") from None
                raise
        if self.install_failed:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="install_failed",
                translation_placeholders={"failed": "; ".join(self.install_failed)},
            )

    async def _async_install(self, context: Context | None) -> None:
        try:
            # A check running refreshes these repositories: install once it has ended, whatever its result.
            if self._task is not None:
                with contextlib.suppress(HomeAssistantError):
                    await self.async_wait()
            # One at a time: the Marketplace writes its data after each install.
            while self.installing:
                entity_id = self.installing[0]
                state = self.hass.states.get(entity_id)
                # Installed or skipped meanwhile (from the Marketplace, another action): nothing left to do.
                if state is not None and state.state == STATE_ON:
                    try:
                        await self.hass.services.async_call(
                            "update", "install", {ATTR_ENTITY_ID: entity_id}, blocking=True, context=context
                        )
                    except Exception as err:  # noqa: BLE001 - one update must not stop the others
                        name = state.attributes.get("title") or state.name
                        _LOGGER.warning("Could not install the update of %s: %s", name, err)
                        # A new list: the sensor attribute never changes in place.
                        self.install_failed = [*self.install_failed, f"{name}: {err}"]
                self.installing = self.installing[1:]
                self._notify()
        finally:
            self.installing = []
            self._install_task = None
            self._notify()
            # A check due meanwhile runs now; not after an unload, which cancels this task.
            if self.on_install_done is not None and not _cancelling():
                self.on_install_done()

    async def _async_run(self) -> None:
        try:
            marketplace = _marketplace(self.hass)
            installed = marketplace.repositories.list_installed
            repositories = [repo for repo in installed if _in_full_check(marketplace, repo)]
            self.total = len(repositories)
            self.github_connected = bool(marketplace.github_connected)
            self._notify()
            _LOGGER.info("Checking %s Marketplace repositories for updates", self.total)

            # The catalog carries the latest version of every repository it lists: one request per
            # category, nothing against GitHub's rate limit. The Marketplace reads it every 6 hours.
            await marketplace.async_get_all_category_repositories()

            if self.github_connected:
                await self._async_refresh_from_github(repositories)
            else:
                # Anonymous GitHub limit (60 requests an hour): the catalog is the only source. A repository
                # added from a link isn't in it, so nothing checked it.
                for repo in repositories:
                    if _custom(marketplace, repo):
                        _LOGGER.warning(
                            "Could not check %s: no GitHub account connected to the Marketplace", repo.data.full_name
                        )
                        self.failed.append(repo.data.full_name)
                self.done = self.total
            await marketplace.data.async_write()
            # The update entities only change when their coordinator says so.
            for coordinator in marketplace.coordinators.values():
                coordinator.async_update_listeners()
            self.updates = sum(1 for repo in repositories if getattr(repo, "pending_update", False))
            self.state = STATE_IDLE
            _LOGGER.info(
                "Marketplace check done: %s update(s) available, %s repository(ies) failed",
                self.updates,
                len(self.failed),
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Marketplace check failed")
            self.error = str(err)
            self.state = STATE_ERROR
        self.last_check = dt_util.utcnow()
        self._task = None
        self._notify()
        await self._async_save()
        if self.on_done is not None:
            self.on_done()

    async def _async_refresh_from_github(self, repositories: list[Any]) -> None:
        """Fetch every repository again from GitHub, a few at a time, like the Marketplace's own refresh."""
        semaphore = asyncio.Semaphore(PARALLEL_REFRESHES)

        async def refresh(repo: Any) -> None:
            # Being checked by check_repository: take that result instead of refreshing it a second time.
            if (single := self._single.get(str(repo.data.id))) is not None:
                try:
                    if await asyncio.shield(single):
                        self.failed.append(repo.data.full_name)
                    self.done += 1
                    self._notify_progress()
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
                self._notify_progress()

        await asyncio.gather(*(refresh(repo) for repo in repositories))
