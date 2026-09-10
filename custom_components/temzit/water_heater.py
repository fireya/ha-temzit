"""Water heater platform for the Temzit hydromodule (read-only display)."""

from __future__ import annotations

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import ActualState
from .const import (
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    STATE_GWS_HEATING,
    STATE_GWS_ONLY,
    STATE_OFF,
    WH_MODE_COMPRESSOR,
    WH_MODE_COMPRESSOR_TEN,
    WH_MODE_OFF,
    WH_MODE_TEN,
    WH_MODES,
)


def _device_id(entry: ConfigEntry) -> str:
    return f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Temzit water heater entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities([TemzitWaterHeater(coordinator, f"{host}:water_heater", entry)])


class TemzitWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Read-only water heater entity: the unit's GWS (hot water) loop."""

    _attr_has_entity_name = True
    _attr_translation_key = "water_heater"
    _attr_supported_features = WaterHeaterEntityFeature(0)
    _attr_operation_list = WH_MODES
    _attr_min_temp = 0.0
    _attr_max_temp = 75.0
    _attr_target_temperature_step = 1.0
    _attr_precision = 0.1
    _attr_temperature_unit = "°C"

    def __init__(self, coordinator, unique_id: str, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = unique_id

    @property
    def current_temperature(self) -> float:
        return round(self.coordinator.data.t_gws, 1)

    @property
    def target_temperature(self) -> float:
        return round(float(self.coordinator.data.sch_t_gws), 1)

    @property
    def current_operation(self) -> str:
        s: ActualState = self.coordinator.data
        if s.state == STATE_OFF:
            return WH_MODE_OFF
        if s.state in (STATE_GWS_HEATING, STATE_GWS_ONLY):
            if s.compressor1 > 0 and s.bkn_heater:
                return WH_MODE_COMPRESSOR_TEN
            if s.bkn_heater:
                return WH_MODE_TEN
            return WH_MODE_COMPRESSOR
        return WH_MODE_OFF

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
