"""Constants for HACS Refresh."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "hacs_refresh"
HACS_DOMAIN: Final = "hacs"

CONF_SCAN_INTERVAL: Final = "scan_interval"
# Hours between two automatic checks; 0 turns the automatic check off.
DEFAULT_SCAN_INTERVAL: Final = 24
MAX_SCAN_INTERVAL: Final = 168

# Repositories refreshed at the same time: HACS itself fetches them one by one,
# a few in parallel keeps a large install quick without hammering the GitHub API.
PARALLEL_REFRESHES: Final = 4

SERVICE_CHECK_UPDATES: Final = "check_updates"

STATE_IDLE: Final = "idle"
STATE_RUNNING: Final = "running"
STATE_ERROR: Final = "error"
