"""Binary sensor platform: computed status flags not backed by a single register."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import Platform

from .entity import SungrowEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry
    from .sungrow_modbus import SungrowSHx


@dataclass(frozen=True, kw_only=True)
class SungrowBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a computed boolean property on the top-level device."""

    is_on_fn: Callable[[SungrowSHx], bool | None]


_DESCRIPTIONS: tuple[SungrowBinarySensorDescription, ...] = (
    SungrowBinarySensorDescription(
        key="is_pv_generating",
        translation_key="is_pv_generating",
        name="PV generating",
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=lambda device: device.is_pv_generating,
    ),
    SungrowBinarySensorDescription(
        key="is_battery_charging",
        translation_key="is_battery_charging",
        name="Battery charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=lambda device: device.is_battery_charging,
    ),
    SungrowBinarySensorDescription(
        key="is_importing_from_grid",
        translation_key="is_importing_from_grid",
        name="Importing from grid",
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=lambda device: device.is_importing_from_grid,
    ),
    SungrowBinarySensorDescription(
        key="is_running",
        translation_key="is_running",
        name="Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=lambda device: device.status.is_running,
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(SungrowBinarySensor(coordinator, d) for d in _DESCRIPTIONS)


class SungrowBinarySensor(SungrowEntity, BinarySensorEntity):
    """A computed status flag."""

    entity_description: SungrowBinarySensorDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        # These read across several components (or the top-level device), so
        # they are not tied to a single "component" the way SungrowEntity
        # normally expects; pass "info" purely so the base class's __init__
        # has something to look up (unused after init, see _subsystem below).
        super().__init__(
            coordinator, description.key, "info", Platform.BINARY_SENSOR.value
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the computed flag's current value."""
        return self.entity_description.is_on_fn(self.coordinator.device)
