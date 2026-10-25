# Changelog

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
