"""
Base entity for the Sungrow custom integration.

A Sungrow inverter is a single physical device: every entity belongs to the
same device, distinguished only by which library sub-system (``pv``,
``battery``, ``grid``, ...) it reads from.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import legacy_naming
from .const import CONF_LEGACY_NAMING, DOMAIN
from .coordinator import SungrowDataUpdateCoordinator


class SungrowEntity(CoordinatorEntity[SungrowDataUpdateCoordinator]):
    """Common identity + device-info for every Sungrow entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        key: str,
        component: str,
        platform: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._component = component
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        if entry.data.get(CONF_LEGACY_NAMING):
            object_id = legacy_naming.suggested_object_id_for(key, platform)
            if object_id is not None:
                # Setting entity_id itself (rather than the read-only
                # suggested_object_id property, which _attr_* can't
                # override) is what HA's entity platform treats as "this
                # entity suggests its own id" -- the only path that skips
                # has_entity_name's automatic device-name prefixing.
                self.entity_id = f"{platform}.{object_id}"
        info = coordinator.device.info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=info.manufacturer,
            model=info.model,
            name=info.model,
            sw_version=info.firmware_version,
            serial_number=info.serial_number,
        )

    @property
    def _subsystem(self) -> object:
        """The library sub-system object this entity reads from."""
        return getattr(self.coordinator.device, self._component)
