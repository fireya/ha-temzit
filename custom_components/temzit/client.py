"""TCP protocol client for the Temzit hydromodule."""

from __future__ import annotations

import asyncio
import logging
import struct
from dataclasses import dataclass
from typing import Optional

from homeassistant.exceptions import HomeAssistantError

from .const import (
    CMD_ACTUAL_STATE,
    CMD_CONFIG_MAIN,
    CMD_REQCFG,
    CMD_SYNC,
    DEFAULT_PORT,
    WATER_CP,
    WATER_DENSITY_PER_L,
)

_LOGGER = logging.getLogger(__name__)


class TemzitError(HomeAssistantError):
    """Base error for the Temzit integration."""


class TemzitConnectionError(TemzitError):
    """Raised when the device cannot be reached."""


@dataclass
class ActualState:
    """Parsed and calculated state of the hydromodule."""

    state: int
    sched_no: int
    t_outdoor: float
    t_home: float
    t_supply: float
    t_return: float
    t_freon_gas: float
    t_freon_liquid: float
    t_gws: float
    flow: float
    compressor1: int
    compressor2: int
    power_w: float
    ten_state: bool
    bkn_heater: bool
    alarm: int
    fw_major: int
    fw_minor: int
    active_schedule: int
    sched_active: int
    sch_t_home: int
    sch_t_water: int
    sch_t_gws: int
    sch_kkb_limit: int
    sch_ten_mode: int
    sch_gws_mode: int
    day: int
    hour: int
    minute: int
    second: int
    output_power_w: float
    cop: Optional[float]


def _bcd(byte: int) -> int:
    """Decode a BCD byte (two decimal digits) to an int."""
    return ((byte >> 4) & 0x0F) * 10 + (byte & 0x0F)


def _le16(buf: bytes, offset: int) -> int:
    """Read an unsigned 16-bit little-endian value."""
    return struct.unpack_from("<H", buf, offset)[0]


def _checksum_ok(response: bytes) -> bool:
    """Validate the 16-bit checksum: sum of first 62 bytes vs LE word at 62."""
    calc = sum(response[:62]) & 0xFFFF
    recv = struct.unpack_from("<H", response, 62)[0]
    return calc == recv


def _calc_output_power(flow_l_min: float, t_supply: float, t_return: float) -> float:
    """Thermal output from the water loop: Q = m_dot * cp * dT, in watts."""
    mass_kg_s = flow_l_min * WATER_DENSITY_PER_L / 60.0
    return mass_kg_s * WATER_CP * (t_supply - t_return)


def _calc_cop(output_power_w: float, consumed_w: float) -> Optional[float]:
    """COP = output / consumed; None when consumed is zero."""
    if consumed_w == 0:
        return None
    return output_power_w / consumed_w


def parse_actual_state(response: bytes) -> ActualState:
    """Parse a 64-byte ACTUAL_STATE response into an ActualState."""
    a = response[2:62]

    t_supply = _le16(a, 8) / 10.0
    t_return = _le16(a, 10) / 10.0
    flow = 1.75 * _le16(a, 18) + 0.25 * _le16(a, 20) + 9.75
    power_w = _le16(a, 28) * 100.0

    output_power_w = _calc_output_power(flow, t_supply, t_return)
    cop = _calc_cop(output_power_w, power_w)

    return ActualState(
        state=_le16(a, 0),
        sched_no=_le16(a, 2),
        t_outdoor=_le16(a, 4) / 10.0,
        t_home=_le16(a, 6) / 10.0,
        t_supply=t_supply,
        t_return=t_return,
        t_freon_gas=_le16(a, 12) / 10.0,
        t_freon_liquid=_le16(a, 14) / 10.0,
        t_gws=_le16(a, 16) / 10.0,
        flow=flow,
        compressor1=a[22],
        compressor2=a[23],
        power_w=power_w,
        ten_state=_le16(a, 24) != 0,
        bkn_heater=_le16(a, 26) != 0,
        alarm=_le16(a, 30),
        fw_major=a[43],
        fw_minor=a[44],
        active_schedule=a[45],
        sched_active=a[46],
        sch_t_home=a[49],
        sch_t_water=a[50],
        sch_t_gws=a[51],
        sch_kkb_limit=a[52],
        sch_ten_mode=a[53],
        sch_gws_mode=a[54],
        day=_bcd(a[56]),
        hour=_bcd(a[57]),
        minute=_bcd(a[58]),
        second=_bcd(a[59]),
        output_power_w=output_power_w,
        cop=cop,
    )


@dataclass
class DeviceConfig:
    """Parsed device configuration (CONFIG_MAIN response)."""

    mode: int
    t_home: int
    t_water: int
    inertia_home: int
    ten_mode: int
    t_outdoor_ten_start: int
    t_min_kkb: int
    disinfection: int
    gws_mode: int
    t_gws: int
    ext_boiler_mode: int
    kkb_power_limit: int
    meter_pulses: int
    weather_compensation: int
    collector_off: int
    collector_on: int
    cn_relay_mode: int
    t_gws_max_kkb: int
    flowmeter_type: int
    overheat_action: int
    sc_mode: int
    overheat_t: int
    kkb1_type: int


def parse_config(response: bytes) -> DeviceConfig:
    """Parse a 64-byte CONFIG_MAIN response into a DeviceConfig."""
    a = response[2:32]
    return DeviceConfig(
        mode=a[0],
        t_home=a[1],
        t_water=a[2],
        inertia_home=a[3] >> 4,
        ten_mode=a[3] & 0x0F,
        t_outdoor_ten_start=a[4],
        t_min_kkb=a[5],
        disinfection=a[6] >> 4,
        gws_mode=a[6] & 0x0F,
        t_gws=a[7],
        ext_boiler_mode=a[8],
        kkb_power_limit=a[9],
        meter_pulses=a[17],
        weather_compensation=a[18],
        collector_off=a[19] >> 4,
        collector_on=a[19] & 0x0F,
        cn_relay_mode=a[20],
        t_gws_max_kkb=a[21],
        flowmeter_type=a[22],
        overheat_action=a[23] >> 3,
        sc_mode=a[23] & 0x07,
        overheat_t=a[24],
        kkb1_type=a[25],
    )


class TemzitClient:
    """Minimal TCP client for the Temzit hydromodule (port 333)."""

    def __init__(self, host: str, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port

    async def get_actual_state(self) -> ActualState:
        """Send SYNC and return the parsed, validated state."""
        command = bytes([CMD_SYNC, 0x00])
        response = await self._exchange(command, 64)

        if response[0] != CMD_ACTUAL_STATE:
            raise TemzitError(
                f"Expected ACTUAL_STATE (0x{CMD_ACTUAL_STATE:02X}), "
                f"got 0x{response[0]:02X}"
            )

        if not _checksum_ok(response):
            _LOGGER.warning("Checksum mismatch in ACTUAL_STATE response")

        return parse_actual_state(response)

    async def get_config(self) -> DeviceConfig:
        """Send REQCFG and return the parsed device configuration."""
        command = bytes([CMD_REQCFG, 0x00])
        response = await self._exchange(command, 64, timeout=15)

        if response[0] != CMD_CONFIG_MAIN:
            raise TemzitError(
                f"Expected CONFIG_MAIN (0x{CMD_CONFIG_MAIN:02X}), "
                f"got 0x{response[0]:02X}"
            )

        if not _checksum_ok(response):
            _LOGGER.warning("Checksum mismatch in CONFIG_MAIN response")

        return parse_config(response)

    async def _exchange(self, command: bytes, expected_length: int, timeout: float = 5) -> bytes:
        """Open a short-lived TCP connection, send a command, read the reply."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, OSError) as err:
            raise TemzitConnectionError(
                f"Cannot connect to {self.host}:{self.port}: {err}"
            ) from err

        try:
            writer.write(command)
            await writer.drain()
            return await asyncio.wait_for(
                reader.readexactly(expected_length),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, OSError) as err:
            raise TemzitConnectionError(
                f"Communication error with {self.host}:{self.port}: {err}"
            ) from err
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
