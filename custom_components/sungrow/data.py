"""Custom types for the Sungrow custom integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from modbus_connection import ModbusConnection

    from .coordinator import SungrowDataUpdateCoordinator


type SungrowConfigEntry = ConfigEntry[SungrowData]


@dataclass
class SungrowData:
    """Runtime data for the Sungrow custom integration."""

    connection: ModbusConnection
    coordinator: SungrowDataUpdateCoordinator
