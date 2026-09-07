"""Custom types for the Sungrow custom integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import SungrowDataUpdateCoordinator


type SungrowConfigEntry = ConfigEntry[SungrowDataUpdateCoordinator]
