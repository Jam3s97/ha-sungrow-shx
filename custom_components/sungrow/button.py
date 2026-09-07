"""
Button platform: inverter start/stop.

These write the control code documented in
``sungrow_modbus.enums.InverterControlCommand`` directly (see
``SungrowSHx.async_start``/``async_stop``); they are not backed by a
readable/writable register pair the way every other control entity is, so
they don't come from :mod:`.field_index`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory

from .entity import SungrowEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry
    from .sungrow_modbus import SungrowSHx


@dataclass(frozen=True, kw_only=True)
class SungrowButtonDescription(ButtonEntityDescription):
    """Describes an inverter control action."""

    press_fn: Callable[[SungrowSHx], object]


_DESCRIPTIONS: tuple[SungrowButtonDescription, ...] = (
    SungrowButtonDescription(
        key="start_inverter",
        translation_key="start_inverter",
        name="Start inverter",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda device: device.async_start(),
    ),
    SungrowButtonDescription(
        key="stop_inverter",
        translation_key="stop_inverter",
        name="Stop inverter",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda device: device.async_stop(),
    ),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow buttons."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(SungrowButton(coordinator, d) for d in _DESCRIPTIONS)


class SungrowButton(SungrowEntity, ButtonEntity):
    """A write-only inverter control action."""

    entity_description: SungrowButtonDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key, "info")
        self.entity_description = description

    async def async_press(self) -> None:
        """Send the control command."""
        await self.entity_description.press_fn(self.coordinator.device)
        await self.coordinator.async_request_refresh()
