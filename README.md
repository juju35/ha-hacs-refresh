# ha-hacs-refresh

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HACS Validation](https://github.com/juju35/ha-hacs-refresh/actions/workflows/hacs.yml/badge.svg)](https://github.com/juju35/ha-hacs-refresh/actions/workflows/hacs.yml)
[![Validate](https://github.com/juju35/ha-hacs-refresh/actions/workflows/validate.yml/badge.svg)](https://github.com/juju35/ha-hacs-refresh/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/juju35/ha-hacs-refresh)](https://github.com/juju35/ha-hacs-refresh/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<p align="center"><img src="custom_components/hacs_refresh/brand/icon.png" alt="HACS Refresh" width="120"></p>

Home Assistant integration that checks every repository downloaded with [HACS](https://hacs.xyz) for updates, on the server: with a button, an action, a progress sensor and a check interval set in the integration options.

HACS itself only checks downloaded custom repositories every 48 hours, and its own "update information" button works one repository at a time from the browser. HACS Refresh checks them all at once, in the background, even when no dashboard is open.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=juju35&repository=ha-hacs-refresh&category=integration)

## Features

- **Check for updates** button and `hacs_refresh.check_updates` action: every repository downloaded with HACS is fetched again from GitHub, four at a time, and HACS' update entities are refreshed
- **`hacs_refresh.check_repository`** action: checks only the repositories behind the HACS update entities you give, and waits for the result
- **Automatic check** at the interval set in the integration options (24 hours by default, `0` to turn it off)
- **Status** sensor (`idle`, `running`, `error`) with the progress (`done` / `total`), the number of updates found and the repositories that failed
- **Last check** sensor (timestamp)
- One failing repository doesn't stop the others; a check never runs twice at the same time
- Used by the [System Monitor Card](https://github.com/juju35/ha-system-monitor-card) for its HACS section
- English and French

## Prerequisites

- [HACS](https://hacs.xyz) 2.x installed and set up
- `hacs_refresh.check_updates` is for administrators, like HACS itself; `hacs_refresh.check_repository` (one repository at a time, like HACS' "Update information") and the button are open to every user

## Installation

### Via HACS (recommended)

Click the button below to add the repository directly:

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=juju35&repository=ha-hacs-refresh&category=integration)

Then click **Download** and restart Home Assistant.

Or manually:

1. Open HACS → **⋮** (top right) → **Custom repositories**
2. Add `https://github.com/juju35/ha-hacs-refresh` — Type: **Integration**
3. Search for **HACS Refresh** and click **Download**
4. Restart Home Assistant

### Manual

Copy `custom_components/hacs_refresh/` to `/config/custom_components/hacs_refresh/`, then restart Home Assistant.

## Configuration

[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hacs_refresh)

**Settings → Devices & services → Add integration → HACS Refresh**, then choose the check interval. Change it later with the **Configure** button.

| Option | Default | Description |
|---|---|---|
| Check interval | 24 h | Hours between two automatic checks, from 1 to 168. `0` turns the automatic check off |

### Entities

| Entity | Description |
|---|---|
| `button.hacs_refresh_check_for_updates` | Starts a check. Unavailable while one is running |
| `sensor.hacs_refresh_status` | `idle`, `running` or `error`. Attributes: `done`, `total`, `updates`, `failed` (list of `owner/repo`), `error`, `checking` (update entities being checked by `check_repository`) |
| `sensor.hacs_refresh_last_check` | End of the last check |

### Action `hacs_refresh.check_updates`

| Field | Default | Description |
|---|---|---|
| `wait` | `false` | Wait until every repository has been checked before the action ends |

Check every night and get notified of the updates found:

```yaml
triggers:
  - trigger: time
    at: "04:00:00"
actions:
  - action: hacs_refresh.check_updates
    data:
      wait: true
  - condition: template
    value_template: "{{ state_attr('sensor.hacs_refresh_status', 'updates') | int(0) > 0 }}"
  - action: notify.mobile_app_phone
    data:
      message: "{{ state_attr('sensor.hacs_refresh_status', 'updates') }} HACS update(s) available"
```

### Action `hacs_refresh.check_repository`

| Field | Description |
|---|---|
| `entity_id` | HACS update entities (`update.*` of platform `hacs`) of the repositories to check |

The action ends once the repositories are checked, and fails with the reason if one could not be. It doesn't change the status or the last check, which belong to the full check.

```yaml
action: hacs_refresh.check_repository
target:
  entity_id: update.mushroom_update
```

## How it works

HACS has no action to check everything: its frontend refreshes one repository at a time over its websocket API. HACS Refresh does, for every downloaded repository, what that websocket command does for one: it asks the repository to update its information from GitHub, saves HACS' data, then tells HACS' update entities to refresh. The update entities (`update.*` of platform `hacs`) then show the new latest versions, like after a manual refresh in HACS.

This relies on HACS' internal object (`hass.data["hacs"]`), as HACS' own websocket commands do. The integration checks that the attributes it needs exist: if a future HACS version changes them, the action fails with a clear message instead of breaking Home Assistant.

Checks go through HACS' GitHub client, so they count towards HACS' GitHub API rate limit (5,000 requests per hour with the token HACS asked for at setup).

To debug:

```yaml
logger:
  logs:
    custom_components.hacs_refresh: debug
```

## Development

```bash
pip install -r requirements_test.txt && pytest
```

The tests use a stand-in for HACS' internal object (`tests/conftest.py`).

### Releasing

1. Bump the version in `custom_components/hacs_refresh/manifest.json`
2. Add a `## <version>` section at the top of [CHANGELOG.md](CHANGELOG.md)
3. Push to `main`: the **Release** workflow creates the tag and the GitHub release with the changelog section as notes

## Translations

The integration follows the language of Home Assistant. Currently supported:

| Language | Code |
|---|---|
| English | `en` |
| Français | `fr` |

Contributions for additional languages are welcome!

## License

[MIT](LICENSE)

Not affiliated with HACS.
