"""Sensors: status of the check with its progress, and the time of the last check."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HacsRefreshConfigEntry
from .const import STATE_ERROR, STATE_IDLE, STATE_RUNNING
from .entity import HacsRefreshEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: HacsRefreshConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            StatusSensor(entry.runtime_data, entry.entry_id, "status"),
            LastCheckSensor(entry.runtime_data, entry.entry_id, "last_check"),
        ]
    )


class StatusSensor(HacsRefreshEntity, SensorEntity):
    """idle / running / error, with the progress as attributes."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [STATE_IDLE, STATE_RUNNING, STATE_ERROR]

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
            "failed": r.failed,
            "error": r.error,
        }


class LastCheckSensor(HacsRefreshEntity, SensorEntity):
    """End of the last check, scheduled or manual."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> datetime | None:
        return self.refresher.last_check
