# HACS Refresh — Agent Context

## Purpose
Home Assistant custom integration that checks every repository downloaded with HACS for updates, on the server, on demand (button, action) and at an interval set in the options. Used by the System Monitor Card's HACS section.

## Architecture

```
custom_components/hacs_refresh/
├── __init__.py      # Actions check_updates (admin) and check_repository (everyone), entry setup, time interval
├── refresher.py     # HacsRefresher: runs the check, keeps state/progress, notifies entities;
│                    #   async_check_repositories: update entity → repository by unique_id (= repository id)
├── config_flow.py   # Single entry, aborts without HACS; options: scan_interval (hours, 0 = off)
├── button.py        # button.*_check_for_updates (unavailable while running)
├── sensor.py        # status (enum idle/running/error + done/total/updates/failed/error), last_check
├── entity.py        # Shared service device, listener on HacsRefresher
├── const.py / icons.json / services.yaml / translations/{en,fr}.json / brand/
```

## HACS internals used (same as HACS' `hacs/repository/refresh` websocket command)
- `hass.data["hacs"]`: `repositories.list_downloaded`, `repository.update_repository(ignore_issues=True, force=True)`, `data.async_write()`, `coordinators[category].async_update_listeners()`, `system.disabled` / `disabled_reason`, `common.categories`.
- `_hacs()` checks these exist and raises `HacsNotAvailableError` with a clear message otherwise. Keep that check in sync if more attributes are used.
- `homeassistant.update_entity` on HACS update entities is a no-op: don't rely on it.

## Release
Bump `version` in manifest.json and add its CHANGELOG.md section; pushing to main publishes `vX.Y.Z` with `hacs_refresh.zip` when that tag doesn't exist yet. Rerun notes with the "Update release notes" workflow (input `tag`).

## Tests
`pip install -r requirements_test.txt && pytest` — HACS is a stand-in object (`tests/conftest.py`).
