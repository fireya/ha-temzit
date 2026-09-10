"""Climate platform for the Temzit hydromodule (read-only display)."""

from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import ActualState
from .const import (
    CLIMATE_PRESET_GWS,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    STATE_COOLING,
    STATE_GWS_HEATING,
    STATE_GWS_ONLY,
    STATE_OFF,
)


def _device_id(entry: ConfigEntry) -> str:
    return f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Temzit climate entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]
    async_add_entities([TemzitClimate(coordinator, f"{host}:climate", entry)])


class TemzitClimate(CoordinatorEntity, ClimateEntity):
    """Read-only climate entity: the unit's underfloor-heating loop."""

    _attr_name = None
    _attr_has_entity_name = True
    _attr_translation_key = "climate"
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [CLIMATE_PRESET_GWS]
    _attr_min_temp = 0.0
    _attr_max_temp = 50.0
    _attr_target_temperature_step = 1.0
    _attr_precision = 0.1
    _attr_temperature_unit = "°C"

    def __init__(self, coordinator, unique_id: str, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = unique_id

    @property
    def current_temperature(self) -> float:
        return round(self.coordinator.data.t_return, 1)

    @property
    def target_temperature(self) -> float:
        return round(float(self.coordinator.data.sch_t_water), 1)

    @property
    def hvac_mode(self) -> HVACMode:
        s: ActualState = self.coordinator.data
        if s.state == STATE_OFF:
            return HVACMode.OFF
        if s.compressor1 > 0:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        s: ActualState = self.coordinator.data
        if s.state == STATE_OFF or s.compressor1 == 0:
            return HVACAction.OFF
        if s.state == STATE_COOLING:
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def preset_mode(self) -> str | None:
        s: ActualState = self.coordinator.data
        if s.state in (STATE_GWS_HEATING, STATE_GWS_ONLY):
            return CLIMATE_PRESET_GWS
        return None

    @property
    def extra_state_attributes(self) -> dict:
        s: ActualState = self.coordinator.data
        return {
            "power_w": s.power_w,
            "cop": s.cop,
            "flow_l_min": s.flow,
        }

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
