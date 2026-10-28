# HACS Refresh — Agent Context

## Purpose
Home Assistant custom integration that checks every repository downloaded with HACS for updates, on the server, on demand (button, action) and at an interval set in the options. Used by the System Monitor Card's HACS section.

## Architecture

```
custom_components/hacs_refresh/
├── __init__.py      # Actions check_updates and check_repository (every user, like the button), entry setup, automatic check
│                    #   (async_call_later on last_check + interval; overdue → runs at async_at_started)
├── refresher.py     # HacsRefresher: runs the check (entry background task, cancelled on unload), keeps state/progress,
│                    #   notifies entities; Store `hacs_refresh` keeps since/last_check/updates across restarts;
│                    #   async_check_repositories: update entity → repository by unique_id (= repository id); waits for a running
│                    #   full check (fails with its error / failed repos); repositories already checked by another call: waits for
│                    #   their future in `_single` (repo id → error|None), or check them itself if that future is cancelled;
│                    #   the full check also takes `_single` results instead of refreshing twice.
│                    #   async_wait: entry unload cancels the task → HomeAssistantError(check_cancelled), not a
│                    #   raw CancelledError (unless the caller itself was cancelled)
├── config_flow.py   # Single entry, aborts without HACS; options: scan_interval (hours, 0 = off)
├── button.py        # button.*_check_for_updates (unavailable while running)
├── sensor.py        # status (enum idle/running/error + done/total/updates/failed/error), last_check
├── entity.py        # Shared service device, listener on HacsRefresher
├── const.py / icons.json / services.yaml / translations/{en,fr}.json
```

## HACS internals used (same as HACS' `hacs/repository/refresh` websocket command)
- `hass.data["hacs"]`: `repositories.list_downloaded`, `repository.update_repository(ignore_issues=True, force=True)`, `data.async_write()`, `coordinators[category].async_update_listeners()`, `system.disabled` / `disabled_reason`, `common.categories`.
- `_hacs()` checks these exist and raises `HacsNotAvailableError` with a clear message otherwise. Keep that check in sync if more attributes are used.
- Error messages are translated: `translation_key` under `exceptions` in translations/{en,fr}.json (no URL in the strings: hassfest refuses them, pass them as placeholders).
- `homeassistant.update_entity` on HACS update entities is a no-op: don't rely on it.

## Release
Bump `version` in manifest.json and add its CHANGELOG.md section; pushing to main publishes `vX.Y.Z` with `hacs_refresh.zip` when that tag doesn't exist yet. Rerun notes with the "Update release notes" workflow (input `tag`).

## Tests
`pip install -r requirements_test.txt && pytest` — HACS is a stand-in object (`tests/conftest.py`). Job `tests` runs on Python 3.14, i.e. the latest Home Assistant (2026.3+ needs Python 3.14; 3.13 would silently resolve to 2026.2) and prints its version as an annotation; job `pytest-min-ha` runs the suite on HA 2024.12.0. An autouse fixture (`tests/conftest.py`, `no_deprecated_calls`) fails any test during which Home Assistant reports a deprecated call naming `hacs_refresh`, and CI turns those reports into annotations.
