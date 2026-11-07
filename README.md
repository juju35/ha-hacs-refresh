# ha-marketplace-refresh

[![Marketplace](https://img.shields.io/badge/Marketplace-Custom-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![HACS Validation](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/hacs.yml/badge.svg)](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/hacs.yml)
[![Validate](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/validate.yml/badge.svg)](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/validate.yml)
[![Lint](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/lint.yml/badge.svg)](https://github.com/juju35/ha-marketplace-refresh/actions/workflows/lint.yml)
[![Release](https://img.shields.io/github/v/release/juju35/ha-marketplace-refresh)](https://github.com/juju35/ha-marketplace-refresh/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/juju35/ha-marketplace-refresh/blob/main/LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/julienstep9)

<p align="center"><img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/custom_components/marketplace_refresh/brand/icon.png" alt="Marketplace Refresh" width="120"></p>

Home Assistant integration that checks every repository installed from the [Marketplace](https://www.home-assistant.io/integrations/marketplace/) (the built-in successor of HACS since Home Assistant 2026.11) for updates, on the server: with a button, an action, a progress sensor and a check interval set in the integration options.

The Marketplace itself reads its catalog every 6 hours, checks the repositories added from a link every 48 hours, and its own refresh works one repository at a time from the browser. Marketplace Refresh checks them all at once, in the background, even when no dashboard is open. It comes with a Lovelace card showing the check and the updates available.

<p align="center">
  <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card.png" alt="Marketplace Refresh card with updates available" width="420">
  <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-dark.png" alt="Marketplace Refresh card, dark theme" width="420">
</p>

[![Open your Home Assistant instance and open a repository inside the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=juju35&repository=ha-marketplace-refresh&category=integration)

## Features

- **Check for updates** button and `marketplace_refresh.check_updates` action: the catalog is read again, then every installed repository is fetched again from GitHub (with a GitHub account connected to the Marketplace), four at a time, and the Marketplace's update entities are refreshed
- **`marketplace_refresh.check_repository`** action: checks only the repositories behind the Marketplace update entities you give, and waits for the result
- **`marketplace_refresh.install_updates`** action and **Update all** button on the card: installs every update available (or the ones you give), one after the other, administrators only
- **Automatic check** at the interval set in the integration options (24 hours by default, `0` to turn it off), counted from the last check and kept across restarts: an overdue check runs as soon as Home Assistant has started
- **Status** sensor (`idle`, `running`, `error`) with the progress (`done` / `total`), the number of updates found and the repositories that failed
- **Last check** sensor (timestamp), with the check interval and when the next automatic check is due
- **Lovelace card** bundled with the integration: status and progress, last and next check, the updates available and the repositories that couldn't be checked
- One failing repository doesn't stop the others; a check never runs twice at the same time, and `check_repository` waits for a full check that is running instead of starting a second one
- Also used by the [System Monitor Card](https://github.com/juju35/ha-system-monitor-card) for its Marketplace section
- English, French, German, Spanish, Serbian (Cyrillic and Latin), Italian, Dutch, European Portuguese, Polish, Romanian, Danish, Swedish, Bulgarian, Russian, Ukrainian, Hungarian, Slovak, Czech, Slovenian, Latvian and Greek (pt-BR uses the European Portuguese texts)

## Prerequisites

- Home Assistant 2026.11 or later (the Marketplace comes with it; on 2026.10 and older, use [HACS Refresh 1.0.x](https://github.com/juju35/ha-marketplace-refresh/releases/tag/v1.0.3), the previous name of this project, with HACS)
- A GitHub account [connected to the Marketplace](https://www.home-assistant.io/integrations/marketplace/#connecting-github) to check the repositories from GitHub; without one, a check only reads the catalog and the repositories added from a link can't be checked (see [How it works](#how-it-works))
- The button, `marketplace_refresh.check_updates` and `marketplace_refresh.check_repository` are open to every user: they only fetch information, like the Marketplace's own refresh. `marketplace_refresh.install_updates` installs code on the server and is for administrators only, like the Marketplace itself; it also needs the Marketplace warning to have been accepted once in **Settings → Marketplace**

## Installation

### Via the Marketplace (recommended)

Click the button below to add the repository directly:

[![Add to the Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=juju35&repository=ha-marketplace-refresh&category=integration)

Then click **Install** and restart Home Assistant.

Or manually:

1. Open **Settings → Marketplace → Add from link** (top right; this needs a GitHub account connected)
2. Add `https://github.com/juju35/ha-marketplace-refresh` — Type: **Integration**
3. Open **Marketplace Refresh** and click **Install**
4. Restart Home Assistant

### Manual

Copy `custom_components/marketplace_refresh/` to `/config/custom_components/marketplace_refresh/`, then restart Home Assistant.

## Configuration

[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=marketplace_refresh)

**Settings → Devices & services → Add integration → Marketplace Refresh**, then choose the check interval. Change it later with the **Configure** button.

| Option | Default | Description |
|---|---|---|
| Check interval | 24 h | Hours between two automatic checks, from 1 to 168. `0` turns the automatic check off. Counted from the end of the last check (or from the installation before the first one), across restarts |

### Entities

| Entity | Description |
|---|---|
| `button.marketplace_refresh_check_for_updates` | Starts a check. Unavailable while one is running |
| `sensor.marketplace_refresh_status` | `idle`, `running` or `error`. Attributes: `done`, `total`, `updates`, `failed` (list of `owner/repo`), `error`, `checking` (update entities being checked by `check_repository`), `installing` (update entities left to install, the current one first), `install_failed` (`title: error` of the updates that couldn't be installed), `github_connected` (whether a GitHub account was connected to the Marketplace at the last check) |
| `sensor.marketplace_refresh_last_check` | End of the last check. Attributes: `scan_interval` (hours, `0` = automatic check off), `next_check` (when the next automatic check is due, `null` when it is off) |

### Action `marketplace_refresh.check_updates`

| Field | Default | Description |
|---|---|---|
| `wait` | `false` | Wait until every repository has been checked before the action ends. The action then fails if the check failed or could not check a repository (the error lists them), so the steps after it only run on a complete check |

Check every night and get notified of the updates found:

```yaml
triggers:
  - trigger: time
    at: "04:00:00"
actions:
  - action: marketplace_refresh.check_updates
    data:
      wait: true
  - condition: template
    value_template: "{{ state_attr('sensor.marketplace_refresh_status', 'updates') | int(0) > 0 }}"
  - action: notify.mobile_app_phone
    data:
      message: "{{ state_attr('sensor.marketplace_refresh_status', 'updates') }} Marketplace update(s) available"
```

### Action `marketplace_refresh.check_repository`

| Field | Description |
|---|---|
| `entity_id` | Marketplace update entities (`update.*` of platform `marketplace`) of the repositories to check |

The action ends once the repositories are checked, and fails with the reason if one could not be. It doesn't change the status or the last check, which belong to the full check. While a full check runs, it waits for that check to end and fails if that check failed or could not check one of these repositories; a repository already being checked by another call is not checked twice: the action waits for that call's result, and checks it itself if that call is cancelled first. A full check started meanwhile waits for these repositories too instead of checking them again. If Marketplace Refresh is reloaded or removed while the action waits (here or with `wait: true`), it fails with "The check was cancelled".

```yaml
action: marketplace_refresh.check_repository
data:
  entity_id: update.mushroom_update
```

### Action `marketplace_refresh.install_updates`

| Field | Default | Description |
|---|---|---|
| `entity_id` | every Marketplace update entity with an update | Marketplace update entities to install |
| `wait` | `false` | Wait until every update is installed; the action then fails if one couldn't be |

Installs the updates one after the other with `update.install`, in the background (a check running ends first). One failing update doesn't stop the others; the failures are in the status sensor's `install_failed` attribute. Administrators only, like the Marketplace, and the Marketplace warning must have been accepted once in **Settings → Marketplace** (an install from an automation runs without a user); it can't run twice at the same time. Meanwhile, no full check starts: the **Check for updates** button is greyed out, `marketplace_refresh.check_updates` fails with "Updates are being installed", and an automatic check that falls due runs once the installs are done. Integrations need a restart of Home Assistant afterwards, which the Marketplace asks for in **Settings → Repairs**.

```yaml
action: marketplace_refresh.install_updates
data:
  wait: true
```

## Card

The integration serves the **Marketplace Refresh Card** and adds it to the dashboard resources (or loads it on every page when the resources are managed in YAML): no separate install. Add it from the card picker, or:

```yaml
type: custom:marketplace-refresh-card
```

| Updates available | Checking | Installing | Up to date |
|---|---|---|---|
| <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card.png" alt="Card" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-checking.png" alt="Card while checking" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-installing.png" alt="Card while installing" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-ok.png" alt="Card, up to date" width="400"> |
| <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-dark.png" alt="Card, dark theme" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-checking-dark.png" alt="Card while checking, dark theme" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-installing-dark.png" alt="Card while installing, dark theme" width="400"> | <img src="https://raw.githubusercontent.com/juju35/ha-marketplace-refresh/main/screenshots/card-ok-dark.png" alt="Card, up to date, dark theme" width="400"> |

- **Header**: status (up to date, *n* updates, *n* failed, checking *done/total*, error), when the last check ran and when the next automatic one is due, and the **Check for updates** button
- **Progress bar** while a check runs
- **Updates available** (with their number): the repositories with an update, from the Marketplace's own update entities, with the installed and new version, hidden when there is none. A row opens the update entity, to install it or read the release notes
- **Update all (*n*)**: installs every update listed, one after the other, after a confirmation at the top of the card (administrators only). The rows being installed and the number left show the progress
- **Could not be installed**: the updates that failed, with the error
- **Could not be checked**: the repositories the last check couldn't fetch (and, without a GitHub account connected, the ones added from a link, with a line saying why), and the error of a check that failed

Every option is in the visual editor:

| Option | Default | Description |
|---|---|---|
| `entity` | found automatically | The **Status** sensor |
| `title` | Marketplace updates | Card title |
| `show_updates` | `true` | Updates available |
| `show_failed` | `true` | Repositories that couldn't be checked, and the error of a failed check |
| `check_button` | `true` | **Check for updates** button in the header |
| `install_button` | `true` | **Update all** button on the updates available (administrators only) |
| `hide_when_ok` | `false` | Hide the card while everything is up to date (it shows while checking, with an update or an error, and always while editing the dashboard) |
| `language` | Home Assistant's | `en`, `fr`, `de`, `es`, `sr`, `sr-Latn`, `it`, `nl`, `pt`, `pl`, `ro`, `da`, `sv`, `bg`, `ru`, `uk`, `hu`, `sk`, `cs`, `sl`, `lv` or `el` |

The [System Monitor Card](https://github.com/juju35/ha-system-monitor-card) also shows the Marketplace extensions with their update status, and its **Check for updates** button presses this integration's button.

## How it works

The Marketplace has no action to check everything: its panel refreshes one repository at a time over its websocket API. A full check here:

1. reads the catalog again, as the Marketplace does every 6 hours: one request per content type, no GitHub API call, and it carries the latest version of every catalog repository;
2. with a GitHub account connected to the Marketplace, does for every installed repository what the Marketplace's `marketplace/repository/refresh` command does for one: it asks the repository to update its information from GitHub, four at a time, saves the Marketplace's data, then tells its update entities to refresh.

The update entities (`update.*` of platform `marketplace`) then show the new latest versions, like after a manual refresh in the Marketplace.

Without a GitHub account connected, the Marketplace runs on GitHub's anonymous limit (60 requests an hour), far too small to fetch every repository: a check then only reads the catalog, and the repositories added from a link, which the catalog doesn't list, are reported as "could not be checked". `check_repository` always asks GitHub, as the Marketplace's own refresh does.

This relies on the Marketplace manager (the `runtime_data` of its config entry), as the Marketplace's own websocket commands do. The integration checks that the attributes it needs exist: if a future Home Assistant version changes them, the action fails with a clear message instead of breaking Home Assistant.

Checks go through the Marketplace's GitHub client, so they count towards its GitHub API rate limit (5,000 requests per hour with a connected account).

To debug:

```yaml
logger:
  logs:
    custom_components.marketplace_refresh: debug
```

## Development

```bash
pip install -r requirements_test.txt && pytest
node --test test/*.test.mjs        # card
python scripts/screenshots.py      # README screenshots (Playwright)
```

The tests use a stand-in for the Marketplace manager (`tests/conftest.py`).

### Releasing

1. Bump the version in `custom_components/marketplace_refresh/manifest.json`, `const.py` (`VERSION`) and the card (`MARKETPLACE_REFRESH_CARD_VERSION`)
2. Add a `## <version>` section at the top of [CHANGELOG.md](https://github.com/juju35/ha-marketplace-refresh/blob/main/CHANGELOG.md)
3. Push to `main`: once **Validate**, **Lint** and **HACS Validation** (the `hacs/action` check of `hacs.json`, which the Marketplace still uses) have passed on that commit, the **Release** workflow creates the tag and the GitHub release with the changelog section as notes

## Translations

The integration follows the language of Home Assistant. Currently supported:

| Language | Code |
|---|---|
| English | `en` |
| Français | `fr` |
| Deutsch | `de` |
| Español | `es` |
| Српски | `sr` |
| Srpski (latinica) | `sr-Latn` |
| Italiano | `it` |
| Nederlands | `nl` |
| Português (Portugal) | `pt` (pt-BR uses the European Portuguese texts) |
| Polski | `pl` |
| Română | `ro` |
| Dansk | `da` |
| Svenska | `sv` |
| Български | `bg` |
| Русский | `ru` |
| Українська | `uk` |
| Magyar | `hu` |
| Slovenčina | `sk` |
| Čeština | `cs` |
| Slovenščina | `sl` |
| Latviešu | `lv` |
| Ελληνικά | `el` |

Contributions for additional languages are welcome!

## License

[MIT](https://github.com/juju35/ha-marketplace-refresh/blob/main/LICENSE)

Not affiliated with the Home Assistant project or HACS.

## Support

If you find this project useful, you can support its development:

<a href="https://buymeacoffee.com/julienstep9"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="50"></a>
