# Marketplace Refresh — Agent Context

## Purpose
Home Assistant custom integration that checks every repository installed from the Marketplace (built into Home Assistant since 2026.11, successor of HACS) for updates, on the server, on demand (button, action) and at an interval set in the options. Used by the System Monitor Card's Marketplace section. Previously named HACS Refresh (`hacs_refresh`, releases ≤ 1.0.3, for HACS on HA ≤ 2026.10). It bundles a Lovelace card with the check and the updates available.

## Architecture

```
custom_components/marketplace_refresh/
├── __init__.py      # Static path + dashboard resource for the card; actions check_updates and check_repository (every user, like the button),
│                    #   install_updates (admin service), entry setup, automatic check
│                    #   (async_call_later on last_check + interval; overdue → runs at async_at_started; skipped because the Marketplace
│                    #   is unavailable → retried after min(interval, 1 h)); check_updates wait: true → raise_for_result()
├── refresher.py     # MarketplaceRefresher: runs the check (entry background task, cancelled on unload): catalog refresh
│                    #   (`async_get_all_category_repositories`), then `update_repository(force=True)` on every installed repo only
│                    #   when `github_connected` (else custom repos → `failed`, `github_connected` attribute False); keeps state/progress,
│                    #   notifies entities; Store `marketplace_refresh` keeps since/last_check/updates across restarts;
│                    #   async_check_repositories: update entity → repository by unique_id (= repository id); waits for a running
│                    #   full check (fails with its error / failed repos; repositories outside `common.categories` are checked after it); repositories already checked by another call: waits for
│                    #   their future in `_single` (repo id → error|None), or check them itself if that future is cancelled;
│                    #   the full check also takes `_single` results instead of refreshing twice.
│                    #   async_wait: entry unload cancels the task → HomeAssistantError(check_cancelled), not a
│                    #   raw CancelledError (unless the caller itself was cancelled)
│                    #   install: async_start_install → background task calling update.install one entity at a time
│                    #   (waits for a running check first; context of the caller); `installing` (left, current first) /
│                    #   `install_failed` on the status sensor; a second install → ServiceValidationError(install_running)
│                    #   while installing, async_start → ServiceValidationError(check_while_installing); the scheduler skips
│                    #   and `on_install_done` (not called on unload) reschedules, so a check due meanwhile runs after the installs
├── config_flow.py   # Single entry, aborts without the `marketplace` component; options: scan_interval (hours, 0 = off)
├── button.py        # button.*_check_for_updates (unavailable while a check runs or updates are installed)
├── sensor.py        # status (enum idle/running/error + done/total/updates/failed/error), last_check (+ scan_interval/next_check)
├── entity.py        # Shared service device, listener on MarketplaceRefresher
├── frontend/marketplace-refresh-card.js   # custom:marketplace-refresh-card: status sensor + last check + button, Marketplace update entities (platform marketplace, state on),
│                                   #   "Update all (n)" for admins → confirmation at the top of the card → install_updates with the ids listed
├── const.py / icons.json / services.yaml / translations/{en,fr,de,es,sr,sr-Latn,it,nl,pt,pt-BR,pl,ro,da,sv,bg,ru,uk,hu,sk,cs,sl,lv,el}.json (pt-BR = copy of pt)
```

## Marketplace internals used (same as the `marketplace/repository/refresh` websocket command)
- The manager is `hass.config_entries.async_loaded_entries("marketplace")[0].runtime_data` (`homeassistant.components.marketplace.base.MarketplaceManager`, single entry); never imported, read through `_loaded_marketplace()` (patched in tests). Attributes: `repositories.list_installed`, `repositories.is_default(id)` (False for a repo added from a link), `repository.update_repository(ignore_issues=True, force=True)`, `data.async_write()`, `coordinators[category].async_update_listeners()`, `system.disabled` / `disabled_reason`, `common.categories`, `github_connected`, `async_get_all_category_repositories()` (catalog, one request per category, no GitHub call).
- Without `github_connected` the Marketplace is on GitHub's anonymous limit (60/h): a full check reads the catalog only and lists the custom repositories in `failed`; `check_repository` still calls `update_repository` (anonymous, like the Marketplace panel). `update.install` on a Marketplace entity fails with `warning_not_accepted` until an admin accepted the Marketplace warning.
- `_marketplace()` checks these exist and raises `MarketplaceNotAvailableError` with a clear message otherwise. Keep that check in sync if more attributes are used.
- Error messages are translated: `translation_key` under `exceptions` in translations/{en,fr,de,es,sr,sr-Latn,it,nl,pt,pl,ro,da,sv,bg,ru,uk,hu,sk,cs,sl,lv,el}.json (no URL in the strings: hassfest refuses them, pass them as placeholders).
- `homeassistant.update_entity` on Marketplace update entities is a no-op: don't rely on it.

## Card
Served at `/marketplace_refresh/marketplace-refresh-card.js` and added to the dashboard resources (storage mode) or loaded with `add_extra_js_url` (YAML mode); removed with the entry. `_storage_resources()` reads `hass.data["lovelace"]` as a dict (before 2025.2) or a dataclass (`mode`, then `resource_mode` from 2026.2). Counts go through `hrPlural` (Intl.PluralRules: `<key>_one`, `<key>_few` for sr/pl when present, else `<key>_many`). Narrow header: `.heading` flex 1 1 0% with min-width 6ch, `.pill` flex 0 1 auto (no max-width): `_fitPill()` (after each render, on a ResizeObserver of the host and once fonts are ready) measures the label at full size and sets `.pill.compact` (dot only) only when it would be cut; under a 170 px container (a phone's 6 columns) the dot is forced and sits on the badge's corner, and `.sub` / `.ilabel` wrap under 200 px; icon buttons `flex: none`. The card finds its entities by `platform` and `translation_key` in `hass.entities` (entity ID suffix as fallback); the updates listed are the Marketplace's update entities that are `on`, the sensor's `updates` count only when there are none.

## Release
Bump `version` in manifest.json, `VERSION` in const.py and `MARKETPLACE_REFRESH_CARD_VERSION` in the card, and add its CHANGELOG.md section; pushing to main publishes `vX.Y.Z` with `marketplace_refresh.zip` when that tag doesn't exist yet, once the Validate (hassfest, tests), Lint and HACS Validation workflows have all passed on that commit (`workflow_run` on each, gated by the "Check required workflows" step). Rerun notes with the "Update release notes" workflow (input `tag`).

## Tests
`pip install -r requirements_test.txt && pytest` — the Marketplace manager is a stand-in object (`tests/conftest.py`, `fake_marketplace`, GitHub connected by default). Card: `node --test test/*.test.mjs` (the card file is evaluated in a `vm` context with stubs). Screenshots: `python scripts/screenshots.py` (Playwright, mock data, English, pictures blocked, 16 px frame). Job `tests` runs on Python 3.14, i.e. the latest Home Assistant (2026.3+ needs Python 3.14; 3.13 would silently resolve to 2026.2) and prints its version as an annotation (no minimum-version job: the minimum, 2026.11, is the current release, and pytest-homeassistant-custom-component has no 2026.11 pin yet). An autouse fixture (`tests/conftest.py`, `no_deprecated_calls`) fails any test during which Home Assistant reports a deprecated call naming `marketplace_refresh`, and CI turns those reports into annotations.
