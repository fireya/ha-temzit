"""Sensor platform for the Temzit hydromodule."""

from __future__ import annotations

from dataclasses import dataclass
from operator import attrgetter
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import ActualState, DeviceConfig
from .const import (
    CONF_HOST,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
    GWS_MODE_NAMES,
    MANUFACTURER,
    MODEL,
    STATE_NAMES,
    kkb_limit_percent,
    ten_mode_percent,
)

C = "°C"


@dataclass(frozen=True)
class TemzitSensor(SensorEntityDescription):
    """A Temzit sensor definition."""

    getter: Callable[[ActualState], Any] | None = None
    enum_map: dict[int, str] | None = None
    suggested_display_precision: int | None = None


def _fw(state: ActualState) -> str:
    return f"{state.fw_major}.{state.fw_minor}"


def _kkb(state: ActualState) -> float | None:
    return kkb_limit_percent(state.sch_kkb_limit)


def _ten(state: ActualState) -> float | None:
    return ten_mode_percent(state.sch_ten_mode)


MEAS = SensorStateClass.MEASUREMENT
PREC1 = 1

SENSORS: tuple[TemzitSensor, ...] = (
    TemzitSensor(
        key="t_outdoor",
        translation_key="t_outdoor",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_outdoor"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_home",
        translation_key="t_home",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_home"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_supply",
        translation_key="t_supply",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_supply"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_return",
        translation_key="t_return",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_return"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_freon_gas",
        translation_key="t_freon_gas",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_freon_gas"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_freon_liquid",
        translation_key="t_freon_liquid",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_freon_liquid"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="t_gws",
        translation_key="t_gws",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=MEAS,
        getter=attrgetter("t_gws"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="flow",
        translation_key="flow",
        native_unit_of_measurement="л/мин",
        state_class=MEAS,
        getter=attrgetter("flow"),
    ),
    TemzitSensor(
        key="compressor1",
        translation_key="compressor1",
        native_unit_of_measurement="Гц",
        state_class=MEAS,
        getter=attrgetter("compressor1"),
    ),
    TemzitSensor(
        key="compressor2",
        translation_key="compressor2",
        native_unit_of_measurement="Гц",
        state_class=MEAS,
        getter=attrgetter("compressor2"),
    ),
    TemzitSensor(
        key="power",
        translation_key="power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=MEAS,
        getter=attrgetter("power_w"),
    ),
    TemzitSensor(
        key="state",
        translation_key="state",
        getter=attrgetter("state"),
        enum_map=STATE_NAMES,
    ),
    TemzitSensor(
        key="sched_no",
        translation_key="sched_no",
        getter=attrgetter("sched_no"),
    ),
    TemzitSensor(
        key="firmware",
        translation_key="firmware",
        getter=_fw,
    ),
    TemzitSensor(
        key="active_schedule",
        translation_key="active_schedule",
        getter=attrgetter("active_schedule"),
    ),
    TemzitSensor(
        key="sched_active",
        translation_key="sched_active",
        getter=attrgetter("sched_active"),
        enum_map=STATE_NAMES,
    ),
    TemzitSensor(
        key="sch_t_home",
        translation_key="sch_t_home",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        getter=attrgetter("sch_t_home"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="sch_t_water",
        translation_key="sch_t_water",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        getter=attrgetter("sch_t_water"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="sch_t_gws",
        translation_key="sch_t_gws",
        native_unit_of_measurement=C,
        device_class=SensorDeviceClass.TEMPERATURE,
        getter=attrgetter("sch_t_gws"),
        suggested_display_precision=PREC1,
    ),
    TemzitSensor(
        key="sch_kkb_limit",
        translation_key="sch_kkb_limit",
        native_unit_of_measurement="%",
        getter=_kkb,
    ),
    TemzitSensor(
        key="sch_ten_mode",
        translation_key="sch_ten_mode",
        native_unit_of_measurement="%",
        getter=_ten,
    ),
    TemzitSensor(
        key="sch_gws_mode",
        translation_key="sch_gws_mode",
        getter=attrgetter("sch_gws_mode"),
        enum_map=GWS_MODE_NAMES,
    ),
    TemzitSensor(
        key="output_power",
        translation_key="output_power",
        native_unit_of_measurement="W",
        device_class=SensorDeviceClass.POWER,
        state_class=MEAS,
        getter=attrgetter("output_power_w"),
    ),
    TemzitSensor(
        key="cop",
        translation_key="cop",
        state_class=MEAS,
        getter=attrgetter("cop"),
    ),
)


def _calc_target_water(s: ActualState, cfg: DeviceConfig | None) -> float:
    """Target return water temp with weather compensation applied."""
    base = float(s.sch_t_water)
    if cfg is None or cfg.weather_compensation == 0:
        return round(base, 1)
    comp = cfg.weather_compensation / 10.0
    return round(base - comp * s.t_outdoor, 1)


def _device_id(entry: ConfigEntry) -> str:
    return f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Temzit sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    config_coordinator = hass.data[DOMAIN].get("config")
    host = entry.data[CONF_HOST]
    entities: list[TemzitSensorEntity] = []
    for desc in SENSORS:
        entities.append(
            TemzitSensorEntity(coordinator, desc, f"{host}:{desc.key}", entry)
        )
    entities.append(
        TemzitTargetWaterEntity(coordinator, config_coordinator, f"{host}:target_water", entry)
    )
    if config_coordinator is not None:
        entities.append(
            TemzitWeatherCompEntity(config_coordinator, f"{host}:weather_comp", entry)
        )
    async_add_entities(entities)


class TemzitSensorEntity(CoordinatorEntity, SensorEntity):
    """A single Temzit sensor bound to the coordinator."""

    def __init__(
        self,
        coordinator,
        desc: TemzitSensor,
        unique_id: str,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._entry = entry
        self._attr_unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_translation_key = desc.translation_key
        self._attr_native_unit_of_measurement = desc.native_unit_of_measurement
        self._attr_device_class = desc.device_class
        self._attr_state_class = desc.state_class
        if desc.suggested_display_precision is not None:
            self._attr_suggested_display_precision = desc.suggested_display_precision

    @property
    def native_value(self) -> Any:
        state: ActualState = self.coordinator.data
        return self._desc.getter(state)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }


class TemzitTargetWaterEntity(CoordinatorEntity, SensorEntity):
    """Target return water temp with weather compensation (from SYNC + CFG)."""

    def __init__(self, coordinator, config_coordinator, unique_id: str, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_coordinator = config_coordinator
        self._entry = entry
        self._attr_unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "target_water"
        self._attr_native_unit_of_measurement = C
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = MEAS
        self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> float:
        state: ActualState = self.coordinator.data
        cfg: DeviceConfig | None = None
        if self._config_coordinator is not None and self._config_coordinator.data is not None:
            cfg = self._config_coordinator.data
        return _calc_target_water(state, cfg)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }


class TemzitWeatherCompEntity(CoordinatorEntity, SensorEntity):
    """Weather compensation factor from device config (CFG)."""

    def __init__(self, config_coordinator, unique_id: str, entry: ConfigEntry) -> None:
        super().__init__(config_coordinator)
        self._entry = entry
        self._attr_unique_id = unique_id
        self._attr_has_entity_name = True
        self._attr_translation_key = "weather_compensation"
        self._attr_state_class = MEAS
        self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> float | None:
        cfg: DeviceConfig | None = self.coordinator.data
        if cfg is None:
            return None
        return cfg.weather_compensation / 10.0

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, _device_id(self._entry))},
            "name": self._entry.data[CONF_HOST],
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
