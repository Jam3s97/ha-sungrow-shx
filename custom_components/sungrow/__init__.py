"""
Custom integration to integrate Sungrow SHx hybrid inverters with Home Assistant.

For more details about this integration, please refer to
https://github.com/Jam3s97/ha-sungrow-shx
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError

from .const import CONF_UNIT_ID
from .coordinator import SungrowDataUpdateCoordinator
from .modbus import build_params
from .sungrow_modbus import SungrowSHx

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SungrowConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SungrowConfigEntry) -> bool:
    """
    Set up Sungrow from a config entry.

    The Modbus unit comes from Home Assistant core's Modbus integration (see
    :mod:`.modbus`), which shares one connection per physical endpoint across
    every integration that asks it for a unit -- so this entry's connection
    is pooled with any other integration or entry talking to the same
    inverter or gateway, instead of opening a competing link of its own.
    """
    params = build_params(dict(entry.data))
    try:
        unit = async_get_unit(hass, entry, params, int(entry.data[CONF_UNIT_ID]))
    except HomeAssistantError as err:
        msg = f"Could not claim the Modbus connection: {err}"
        raise ConfigEntryNotReady(msg) from err

    device = SungrowSHx(unit)
    coordinator = SungrowDataUpdateCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SungrowConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
