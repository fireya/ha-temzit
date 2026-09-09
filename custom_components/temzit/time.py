"""Time platform for the Temzit hydromodule (device clock)."""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import ActualState
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, MANUFACTURER, MODEL


def _device_id(entry: ConfigEntry) -> str:
    return f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Temzit device clock."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities([TemzitTimeEntity(coordinator, f"{host}:clock", entry)])


class TemzitTimeEntity(CoordinatorEntity, TimeEntity):
    """Expose the hydromodule's internal clock as a time entity."""

    def __init__(self, coordinator, unique_id: str, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "clock"

    @property
    def native_value(self) -> dt_time | None:
        state: ActualState = self.coordinator.data
        return dt_time(state.hour, state.minute, state.second)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
