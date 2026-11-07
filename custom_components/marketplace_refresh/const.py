"""Constants for Marketplace Refresh."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "marketplace_refresh"
# Same as manifest.json and the card: the card URL carries it, so that browsers load a new release.
VERSION: Final = "2.0.2"
MARKETPLACE_DOMAIN: Final = "marketplace"

CONF_SCAN_INTERVAL: Final = "scan_interval"
# Hours between two automatic checks; 0 turns the automatic check off.
DEFAULT_SCAN_INTERVAL: Final = 24
MAX_SCAN_INTERVAL: Final = 168

# Repositories refreshed at the same time: the Marketplace itself fetches them one by one,
# a few in parallel keeps a large install quick without hammering the GitHub API.
PARALLEL_REFRESHES: Final = 4

SERVICE_CHECK_UPDATES: Final = "check_updates"
SERVICE_CHECK_REPOSITORY: Final = "check_repository"
SERVICE_INSTALL_UPDATES: Final = "install_updates"

STATE_IDLE: Final = "idle"
STATE_RUNNING: Final = "running"
STATE_ERROR: Final = "error"

# The card bundled with the integration, served by Home Assistant and added to the dashboard resources.
CARD_URL: Final = f"/{DOMAIN}/marketplace-refresh-card.js"
