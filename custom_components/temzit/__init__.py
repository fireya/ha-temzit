"""The Temzit hydromodule integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import TemzitClient
from .config_flow import TemzitConfigFlow  # noqa: F401  (registers the flow)
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, PLATFORMS
from .coordinator import TemzitCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load the platforms for a Temzit config entry."""
    client = TemzitClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    coordinator = TemzitCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Temzit config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries (no-op for now)."""
    return True
