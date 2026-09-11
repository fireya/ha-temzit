"""Binary sensor platform for the Temzit hydromodule."""

from __future__ import annotations

from dataclasses import dataclass
from operator import attrgetter
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import ActualState
from .const import (
    CONF_HOST,
    CONF_PORT,
    DATA_COORDINATOR,
    DEFAULT_PORT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)


@dataclass(frozen=True)
class TemzitBinarySensor(BinarySensorEntityDescription):
    """A Temzit binary sensor definition."""

    getter: Callable[[ActualState], Any] | None = None


BINARY_SENSORS: tuple[TemzitBinarySensor, ...] = (
    TemzitBinarySensor(
        key="ten_state",
        translation_key="ten_state",
        getter=attrgetter("ten_state"),
    ),
    TemzitBinarySensor(
        key="bkn_heater",
        translation_key="bkn_heater",
        getter=attrgetter("bkn_heater"),
    ),
)


def _device_id(entry: ConfigEntry) -> str:
    return f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Temzit binary sensors."""
    coordinator = hass.data[DATA_COORDINATOR][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities(
        TemzitBinarySensorEntity(coordinator, desc, f"{host}:{desc.key}", entry)
        for desc in BINARY_SENSORS
    )


class TemzitBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """A single Temzit binary sensor bound to the coordinator."""

    def __init__(
        self,
        coordinator,
        desc: TemzitBinarySensor,
        unique_id: str,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._entry = entry
        self._attr_unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_translation_key = desc.translation_key

    @property
    def is_on(self) -> bool | None:
        state: ActualState = self.coordinator.data
        return bool(self._desc.getter(state))

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
