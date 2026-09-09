"""Constants for the Temzit hydromodule integration."""

DOMAIN = "temzit"
MANUFACTURER = "Temzit"
MODEL = "Hydromodule"

CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_PORT = 333
SCAN_INTERVAL_SECONDS = 15

PLATFORMS = ["sensor", "binary_sensor", "time"]

# Water physical constants for calculated fields.
WATER_CP = 4186.0  # J/(kg*K)
WATER_DENSITY_PER_L = 1.0  # kg per litre

# Command types.
CMD_SYNC = 0x30
CMD_ACTUAL_STATE = 0x01
CMD_REQCFG = 0x34
CMD_CONFIG_MAIN = 0x02
CMD_CFG = 0x35

# Device operating state (fields 15 and 19 share this scale).
STATE_OFF = 0
STATE_HEATING = 1
STATE_FAST_HEATING = 2
STATE_TEN_ONLY = 3
STATE_COOLING = 4
STATE_GWS_ONLY = 5

STATE_NAMES = {
    0: "off",
    1: "heating",
    2: "fast_heating",
    3: "ten_only",
    4: "cooling",
    5: "gws_only",
}

# GWS (hot water) mode, field 25.
GWS_MODE_AUTO = 0
GWS_MODE_FORCED = 1
GWS_MODE_NAMES = {
    0: "auto",
    1: "forced",
}

# KKB power limit, field 23: raw index -> percent.
KKB_LIMIT_PERCENT = [100, 10, 20, 30, 40, 50, 55, 60, 70, 80, 90]

# TEN mode, field 24: raw index -> percent.
TEN_MODE_PERCENT = [0, 30, 60, 100]


def kkb_limit_percent(raw: int) -> float | None:
    """Map raw KKB limit index to percent."""
    if 0 <= raw < len(KKB_LIMIT_PERCENT):
        return float(KKB_LIMIT_PERCENT[raw])
    return None


def ten_mode_percent(raw: int) -> float | None:
    """Map raw TEN mode index to percent."""
    if 0 <= raw < len(TEN_MODE_PERCENT):
        return float(TEN_MODE_PERCENT[raw])
    return None
