"""Full end-to-end setup test for the Temzit integration.

Runs the real `async_setup_entry` against an actual Home Assistant install,
with the device client mocked, and prints every resulting entity state.

Usage (in a venv that has `homeassistant` installed, e.g. the same version
as your running HA):

    python dev/test_setup.py

Exit code 0 = the whole integration set up cleanly and all entities exist.
"""

from __future__ import annotations

import asyncio
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from homeassistant.config_entries import (  # noqa: E402
    ConfigEntry,
    ConfigEntries,
    ConfigEntryState,
)
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.helpers import device_registry as dr  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from homeassistant.loader import (  # noqa: E402
    DATA_COMPONENTS,
    DATA_INTEGRATIONS,
    DATA_MISSING_PLATFORMS,
    DATA_PRELOAD_PLATFORMS,
)

import custom_components.temzit as integ  # noqa: E402
import custom_components.temzit.client as CL  # noqa: E402


def build_frame() -> bytes:
    """Build a realistic 64-byte ACTUAL_STATE frame with a valid checksum."""
    a = bytearray(60)

    def le16(off: int, v: int) -> None:
        a[off : off + 2] = struct.pack("<H", v)

    le16(0, 1)  # state = heating
    le16(2, 5)  # sched_no
    le16(4, 30)  # t_out 3.0
    le16(6, 285)  # t_home 28.5
    le16(8, 279)  # t_supply 27.9
    le16(10, 270)  # t_return 27.0
    le16(12, 284)  # fregas 28.4
    le16(14, 283)  # frelq 28.3
    le16(16, 476)  # gws 47.6
    le16(18, 1)  # flow part 1
    le16(20, 0)  # flow part 2
    a[22] = 40  # comp1
    a[23] = 0  # comp2
    le16(24, 1)  # ten on
    le16(26, 0)  # bkn off
    le16(28, 7)  # power raw 7 -> 700 W
    a[43] = 52  # fw major
    a[44] = 92  # fw minor
    a[45] = 3  # active_schedule
    a[46] = 1  # sched_active
    a[49] = 16  # sch t_home
    a[50] = 28  # sch t_water
    a[51] = 44  # sch t_gws
    a[52] = 7  # kkb idx 7 -> 60%
    a[53] = 0  # ten idx 0 -> 0%
    a[54] = 0  # gws auto
    a[56] = 0x04  # day
    a[57] = 0x09  # hour 09 (BCD)
    a[58] = 0x30  # minute 30 (BCD)
    a[59] = 0x15  # second 15 (BCD)

    resp = bytearray([0x01, 0x00]) + a
    resp += struct.pack("<H", sum(resp) & 0xFFFF)
    return bytes(resp)


def make_entry() -> ConfigEntry:
    e = ConfigEntry(
        data={"host": "1.2.3.4", "port": 333},
        discovery_keys={},
        domain="temzit",
        minor_version=1,
        options={},
        source="user",
        subentries_data={},
        title="1.2.3.4",
        unique_id="1.2.3.4",
        version=1,
    )
    object.__setattr__(e, "state", ConfigEntryState.SETUP_IN_PROGRESS)
    return e


async def run() -> None:
    frame = build_frame()
    state = CL.parse_actual_state(frame)

    async def fake_get(self):  # noqa: ANN001
        return state

    CL.TemzitClient.get_actual_state = fake_get

    cfg_frame = bytearray([0x02, 0x00]) + bytearray(60)
    cfg_frame[2 + 1] = 16  # t_home
    cfg_frame[2 + 2] = 30  # t_water
    cfg_frame[2 + 18] = 2  # weather_compensation = 2 -> 0.2
    cfg_frame += struct.pack("<H", sum(cfg_frame) & 0xFFFF)
    cfg = CL.parse_config(bytes(cfg_frame))

    async def fake_get_config(self):  # noqa: ANN001
        return cfg

    CL.TemzitClient.get_config = fake_get_config

    hass = HomeAssistant(str(ROOT))
    await hass.async_start()
    hass.config_entries = ConfigEntries(hass, {})
    hass.data[DATA_INTEGRATIONS] = {}
    hass.data[DATA_PRELOAD_PLATFORMS] = set()
    hass.data[DATA_MISSING_PLATFORMS] = {}
    hass.data[DATA_COMPONENTS] = {}
    dr.async_setup(hass)
    await dr.async_load(hass)
    await er.async_get(hass).async_load()

    entry = make_entry()
    hass.config_entries._entries[entry.entry_id] = entry

    async with entry.setup_lock:
        ok = await integ.async_setup_entry(hass, entry)

    states = hass.states.async_all()
    print(f"async_setup_entry returned: {ok}")
    print(f"states: {len(states)}")
    for s in sorted(states, key=lambda x: x.entity_id):
        print("  ", s.entity_id, "=", s.state)

    expected = 24 + 2 + 1 + 1 + 1 + 2  # sensors + binary + time + climate + wh + target_water + weather_comp
    if not ok or len(states) != expected:
        raise SystemExit(f"FAIL: ok={ok}, states={len(states)}, expected={expected}")
    print(f"OK: integration set up, {expected} entities registered")


if __name__ == "__main__":
    asyncio.run(run())
