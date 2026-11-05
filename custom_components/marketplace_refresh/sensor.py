"""Sensors: status of the check with its progress, and the time of the last check."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, ClassVar

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarketplaceRefreshConfigEntry
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, STATE_ERROR, STATE_IDLE, STATE_RUNNING
from .entity import MarketplaceRefreshEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: MarketplaceRefreshConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            StatusSensor(entry.runtime_data, entry.entry_id, "status"),
            LastCheckSensor(entry.runtime_data, entry.entry_id, "last_check"),
        ]
    )


class StatusSensor(MarketplaceRefreshEntity, SensorEntity):
    """idle / running / error, with the progress as attributes."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options: ClassVar[list[str]] = [STATE_IDLE, STATE_RUNNING, STATE_ERROR]

    @property
    def native_value(self) -> str:
        return self.refresher.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        r = self.refresher
        return {
            "done": r.done,
            "total": r.total,
            "updates": r.updates,
            "failed": list(r.failed),
            "error": r.error,
            "checking": sorted(r.checking),
            "installing": list(r.installing),
            "install_failed": list(r.install_failed),
            "github_connected": r.github_connected,
        }


class LastCheckSensor(MarketplaceRefreshEntity, SensorEntity):
    """End of the last check, scheduled or manual."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> datetime | None:
        return self.refresher.last_check

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """The automatic check's interval (hours, 0 = off) and when it is due, for the card."""
        r = self.refresher
        hours = int(r.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        last = r.last_check or r.since
        due = last + timedelta(hours=hours) if hours > 0 and last else None
        return {"scan_interval": hours, "next_check": due.isoformat() if due else None}
