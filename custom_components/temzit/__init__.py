"""The Temzit hydromodule integration."""

from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .client import TemzitClient
from .config_flow import TemzitConfigFlow  # noqa: F401
from .const import (
    CONF_HOST,
    CONF_PORT,
    DATA_COORDINATOR,
    DEFAULT_PORT,
    DOMAIN,
    MIN_CFG_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import TemzitConfigCoordinator, TemzitCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_INTERVALS = "set_intervals"

SERVICE_SET_INTERVALS_SCHEMA = vol.Schema(
    {
        vol.Optional("scan_interval"): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
        vol.Optional("cfg_scan_interval"): vol.All(int, vol.Range(min=MIN_CFG_SCAN_INTERVAL)),
    }
)


def _register_service(hass: HomeAssistant) -> None:
    if DATA_COORDINATOR in hass.data and "service_registered" in hass.data[DATA_COORDINATOR]:
        return

    async def handle_set_intervals(call: ServiceCall) -> None:
        data = hass.data.get(DATA_COORDINATOR, {})
        scan_interval = call.data.get("scan_interval")
        cfg_scan_interval = call.data.get("cfg_scan_interval")
        for entry_id, coordinator in list(data.items()):
            if not isinstance(coordinator, TemzitCoordinator):
                continue
            if scan_interval is not None:
                coordinator.update_interval = timedelta(seconds=scan_interval)
            config_coord = data.get("config")
            if config_coord is not None and cfg_scan_interval is not None:
                config_coord.update_interval = timedelta(seconds=cfg_scan_interval)
        _LOGGER.info(
            "Temzit intervals updated: scan=%ss cfg=%ss",
            scan_interval, cfg_scan_interval,
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_INTERVALS,
        handle_set_intervals,
        schema=SERVICE_SET_INTERVALS_SCHEMA,
    )
    data = hass.data.setdefault(DATA_COORDINATOR, {})
    data["service_registered"] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load the platforms for a Temzit config entry."""
    _register_service(hass)

    client = TemzitClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    coordinator = TemzitCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    config_coordinator = TemzitConfigCoordinator(hass, entry, client)
    try:
        await config_coordinator.async_config_entry_first_refresh()
    except Exception:
        pass

    hass.data.setdefault(DATA_COORDINATOR, {})[entry.entry_id] = coordinator
    hass.data[DATA_COORDINATOR]["config"] = config_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Temzit config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data = hass.data.get(DATA_COORDINATOR, {})
        data.pop(entry.entry_id, None)
    return ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries (no-op for now)."""
    return True
