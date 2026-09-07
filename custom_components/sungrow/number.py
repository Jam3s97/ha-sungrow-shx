"""Number platform: every writable numeric field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from .entity import SungrowEntity
from .field_index import FieldRef, iter_fields
from .unit_mapping import entity_category_for, native_unit_and_device_class

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry


@dataclass(frozen=True, kw_only=True)
class SungrowNumberDescription(NumberEntityDescription):
    """Describes a writable numeric field on one component."""

    component: str
    attribute: str


def _description_for(field: FieldRef) -> SungrowNumberDescription:
    unit, _device_class = native_unit_and_device_class(field)
    number_meta = field.metadata.number
    return SungrowNumberDescription(
        key=field.key,
        translation_key=field.key,
        name=field.name,
        component=field.component,
        attribute=field.attribute,
        native_unit_of_measurement=unit,
        native_min_value=(number_meta.min_value if number_meta else None) or 0,
        native_max_value=(number_meta.max_value if number_meta else None) or 100000,
        native_step=(number_meta.step if number_meta else None) or 1,
        mode=NumberMode.BOX,
        entity_category=entity_category_for(field),
    )


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow numbers: every writable, non-enum, non-boolean field."""
    coordinator = entry.runtime_data.coordinator
    descriptions = [
        _description_for(field)
        for field in iter_fields(coordinator.device)
        if field.is_writable and field.metadata.value_kind == "number"
    ]
    async_add_entities(SungrowNumber(coordinator, d) for d in descriptions)


class SungrowNumber(SungrowEntity, NumberEntity):
    """A writable numeric setting."""

    entity_description: SungrowNumberDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowNumberDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return getattr(self._subsystem, self.entity_description.attribute)

    async def async_set_native_value(self, value: float) -> None:
        """Write the new value to the inverter."""
        await self._subsystem.write(self.entity_description.attribute, value)
        await self.coordinator.async_request_refresh()
