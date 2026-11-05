"""Button that starts the check."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarketplaceRefreshConfigEntry
from .entity import MarketplaceRefreshEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: MarketplaceRefreshConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([CheckUpdatesButton(entry.runtime_data, entry.entry_id, "check_updates")])


class CheckUpdatesButton(MarketplaceRefreshEntity, ButtonEntity):
    """Check every repository installed from the Marketplace for updates."""

    @property
    def available(self) -> bool:
        # Greyed out while a check runs, so it can't be pressed twice, and while updates are installed.
        return not self.refresher.running and not self.refresher.installing_updates

    async def async_press(self) -> None:
        # MarketplaceNotAvailableError is a HomeAssistantError with a translated message.
        self.refresher.async_start()
