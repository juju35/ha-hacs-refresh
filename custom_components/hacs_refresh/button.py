"""Button that starts the check."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import HacsRefreshConfigEntry
from .entity import HacsRefreshEntity
from .refresher import HacsNotAvailableError


async def async_setup_entry(
    hass: HomeAssistant, entry: HacsRefreshConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([CheckUpdatesButton(entry.runtime_data, entry.entry_id, "check_updates")])


class CheckUpdatesButton(HacsRefreshEntity, ButtonEntity):
    """Check every repository downloaded with HACS for updates."""

    @property
    def available(self) -> bool:
        # Greyed out while a check runs, so it can't be pressed twice.
        return not self.refresher.running

    async def async_press(self) -> None:
        try:
            self.refresher.async_start()
        except HacsNotAvailableError as err:
            raise HomeAssistantError(str(err)) from err
