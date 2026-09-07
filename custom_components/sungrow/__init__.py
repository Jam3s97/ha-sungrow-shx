"""
Custom integration to integrate Sungrow SHx hybrid inverters with Home Assistant.

For more details about this integration, please refer to
https://github.com/Jam3s97/ha-sungrow-shx
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryNotReady
from modbus_connection import ModbusError

from .const import CONF_UNIT_ID
from .coordinator import SungrowDataUpdateCoordinator
from .data import SungrowData
from .modbus import build_connection
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

    This integration owns its Modbus connection outright (see
    :mod:`.modbus`): it does not depend on any shared core component, so it
    works standalone as a HACS package.
    """
    connection = build_connection(dict(entry.data))
    try:
        await connection.connect()
    except (ModbusError, OSError) as err:
        msg = f"Could not connect to the inverter: {err}"
        raise ConfigEntryNotReady(msg) from err

    device = SungrowSHx(connection.for_unit(int(entry.data[CONF_UNIT_ID])))
    coordinator = SungrowDataUpdateCoordinator(hass, entry, device)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await connection.close()
        raise

    entry.runtime_data = SungrowData(connection=connection, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SungrowConfigEntry) -> bool:
    """Unload a config entry, closing the Modbus connection it owns."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.connection.close()
    return unloaded
