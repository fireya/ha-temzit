"""Coordinator for the Temzit hydromodule."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import ActualState, DeviceConfig, TemzitClient, TemzitError
from .const import (
    CFG_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
    SCAN_INTERVAL_SECONDS,
)

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

    async def _async_update_data(self) -> ActualState:
        last_err: TemzitError | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self.client.get_actual_state()
            except TemzitError as err:
                last_err = err
                _LOGGER.warning(
                    "Temzit poll failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    err,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise UpdateFailed(
            f"Temzit unavailable after {MAX_RETRIES} attempts: {last_err}"
        ) from last_err


class TemzitConfigCoordinator(DataUpdateCoordinator[DeviceConfig]):
    """Poll the hydromodule with REQCFG (rarely) and expose the device config."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TemzitClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_config_{entry.entry_id}",
            config_entry=entry,
            update_interval=timedelta(seconds=CFG_SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> DeviceConfig:
        last_err: TemzitError | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self.client.get_config()
            except TemzitError as err:
                last_err = err
                _LOGGER.warning(
                    "Temzit config poll failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    err,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise UpdateFailed(
            f"Temzit config unavailable after {MAX_RETRIES} attempts: {last_err}"
        ) from last_err
