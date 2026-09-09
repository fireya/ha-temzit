"""Coordinator for the Temzit hydromodule."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import ActualState, TemzitClient, TemzitError
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class TemzitCoordinator(DataUpdateCoordinator[ActualState]):
    """Poll the hydromodule with SYNC and expose the parsed state."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TemzitClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update(self) -> ActualState:
        try:
            return await self.client.get_actual_state()
        except TemzitError as err:
            raise UpdateFailed(f"Polling Temzit failed: {err}") from err
