# Changelog

## 0.7.0

### What's new
- **HACS Refresh Card**, bundled with the integration and added to the dashboard resources automatically: status and progress bar, last and next check, **Check for updates** button, the HACS repositories with an update (installed → new version, a row opens the update entity) and the repositories that couldn't be checked. Visual editor; English, French, German and Spanish.
- The **Last check** sensor gives `scan_interval` and `next_check` (when the next automatic check is due).

### Maintenance
- Card unit tests, Biome lint, and a Screenshots workflow that renders the README captures (light and dark) on pull requests.

## 0.6.1

### Fixes
- `hacs_refresh.check_updates` with `wait: true` fails when the check failed or could not check a repository, like `hacs_refresh.check_repository`, instead of succeeding (automations no longer act on the previous check's `updates`).
- A scheduled check skipped because HACS is unavailable (rate-limited, still starting) is retried within the hour instead of after a full interval.
- The `failed` attribute of the status sensor no longer changes in place while a check runs.
- "HACS is disabled" no longer shows an untranslated "unknown" when HACS gives no reason.
- `hacs_refresh.check_repository` during a full check also checks the repositories whose category the full check leaves out, instead of reporting success without checking them.

### Maintenance
- CI: the release is published only once Validate (hassfest, tests) has passed on the push to main; vulture is pinned in `requirements_lint.txt` so Dependabot keeps it up to date.
- Tests for the fixes.

## 0.6.0

### Changes
- German and Spanish translations.

## 0.5.1

### Fixes
- HACS installs and updates HACS Refresh from the `hacs_refresh.zip` release asset, so development files are no longer copied to Home Assistant.
- A `hacs_refresh.check_repository` waiting for another call on the same repository no longer reports success when saving the HACS data fails: it checks the repository itself and fails with the error.
- On large installations, the full check updates its progress at most every 0.5 s instead of after every repository, avoiding hundreds of state and recorder writes; the final state is always reported.
- "HACS is disabled" says "unknown" instead of "None" when HACS gives no reason.
- The `hacs_refresh.check_repository` action has its own icon.

### Maintenance
- AGENT.md moved out of the installed integration; brand assets stay under `custom_components/hacs_refresh/brand/` for the HACS brands check but are kept out of the release zip.
- CI: branch cleanup paginates PR lookups, ruff-action pinned to the pre-commit ruff version, stale exempts `confirmed`/`pinned` issues, Dependabot watches `requirements_test.txt`; leftover lint config from the card repositories removed.
- README: the `check_repository` example uses `data:`.

## 0.5.0

### Maintenance
- Removed the unused local `card-js-syntax` pre-commit hook: it was copied from the Lovelace card repositories, but HACS Refresh is a pure Python integration with no `.js` files, so the hook never checked anything and only forced `node` to be installed to run pre-commit locally.

## 0.4.1

### Fixes
- A `hacs_refresh.check_repository` waiting for another call on the same repository checks that repository itself when the other call is cancelled (automation or script stopped, client disconnected), instead of failing with "The check was cancelled (HACS Refresh was reloaded or removed)" without checking it.

### Maintenance
- Test for the fix; the duplication check runs on Node 22.

## 0.4.0

### Changes
- Requires Home Assistant 2024.12 or later (was 2024.11): on 2024.11, **Configure** failed with an error.
- `hacs_refresh.check_repository` called during a full check fails if that check failed or could not check one of its repositories, instead of succeeding.
- A second `hacs_refresh.check_repository` on a repository already being checked waits for the first one's result and fails with the same reason, instead of returning at once.
- A full check started while `hacs_refresh.check_repository` is running uses its result instead of checking the same repositories again.

### Fixes
- `hacs_refresh.check_updates` with `wait: true`, or a `hacs_refresh.check_repository` waiting for a full check, fails with "The check was cancelled" when HACS Refresh is reloaded or removed, instead of a raw error.

### Maintenance
- Tests run on Home Assistant 2026.10 and on the minimum version (2024.12), and fail on any deprecated Home Assistant call; new tests for the fixes.

## 0.3.0

### Changes
- The `hacs_refresh.check_updates` action is open to every user, like the **Check for updates** button and `hacs_refresh.check_repository`: it only fetches information, installing stays with HACS.
- Error messages are translated (English, French).

### Fixes
- The automatic check runs even when Home Assistant restarts more often than the interval: the last check is kept across restarts and an overdue check runs at startup. `last_check` and `updates` no longer go back to unknown after a restart.
- Unloading the entry (options changed, removed) stops a running check, so two full checks no longer run side by side.
- `hacs_refresh.check_repository` called during a full check waits for it, and an entity already being checked is not refreshed twice.
- A HACS version without `disabled_reason` gives the "HACS is disabled" error instead of a bare error.

### Maintenance
- New pytest tests for the fixes.
- CI hardening: actions pinned by commit SHA, read-only token, Dependabot for actions, duplication check with PR annotations.

## 0.2.2

### Maintenance
- Tooling only, no functional change: ruff/Biome/pre-commit, a Lint CI with duplication and dead-code checks, and internal modernizations.

## 0.2.1

### Maintenance
- README: **Screenshots** section, with the HACS section of the System Monitor Card.

## 0.2.0

### What's new
- `hacs_refresh.check_repository` action: checks only the repositories behind the HACS update entities given in `entity_id`, and waits for the result. Open to every user, like the button. Used by the per-extension button of the System Monitor Card.
- The **Status** sensor lists the update entities being checked this way in its `checking` attribute.

## 0.1.0

### What's new
- First release: checks every repository downloaded with HACS for updates on the server, four at a time, then refreshes HACS' update entities.
- **Check for updates** button and `hacs_refresh.check_updates` action (administrators only), with an optional `wait`.
- Automatic check at the interval set in the integration options (24 hours by default, `0` to turn it off).
- **Status** sensor with the progress, the number of updates found and the repositories that failed, and a **Last check** sensor.
- English and French.
