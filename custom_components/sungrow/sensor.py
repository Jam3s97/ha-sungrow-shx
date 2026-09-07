"""Sensor platform: every read-only numeric/string/enum field."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from .entity import SungrowEntity
from .field_index import FieldRef, iter_fields
from .unit_mapping import (
    entity_category_for,
    native_unit_and_device_class,
    state_class_for,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry


@dataclass(frozen=True, kw_only=True)
class SungrowSensorDescription(SensorEntityDescription):
    """Describes a sensor reading one attribute of one component."""

    component: str
    attribute: str


def _description_for(field: FieldRef) -> SungrowSensorDescription:
    if field.metadata.value_kind == "enum":
        options = [option.key for option in field.metadata.enum.options]
        return SungrowSensorDescription(
            key=field.key,
            translation_key=field.key,
            name=field.name,
            component=field.component,
            attribute=field.attribute,
            device_class=SensorDeviceClass.ENUM,
            options=options,
            entity_category=entity_category_for(field),
        )
    if field.metadata.value_kind == "string":
        return SungrowSensorDescription(
            key=field.key,
            translation_key=field.key,
            name=field.name,
            component=field.component,
            attribute=field.attribute,
            entity_category=entity_category_for(field),
        )
    unit, device_class = native_unit_and_device_class(field)
    return SungrowSensorDescription(
        key=field.key,
        translation_key=field.key,
        name=field.name,
        component=field.component,
        attribute=field.attribute,
        native_unit_of_measurement=unit,
        device_class=device_class,
        state_class=state_class_for(field),
        suggested_display_precision=1 if unit is not None else None,
        entity_category=entity_category_for(field),
    )


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow sensors: every read-only field in the library."""
    coordinator = entry.runtime_data
    descriptions = [
        _description_for(field)
        for field in iter_fields(coordinator.device)
        if not field.is_writable
    ]
    async_add_entities(SungrowSensor(coordinator, d) for d in descriptions)


class SungrowSensor(SungrowEntity, SensorEntity):
    """A single read-only value read from a component attribute."""

    entity_description: SungrowSensorDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    def native_value(self) -> object:
        """Return the current value, mapping enums to their option key."""
        value = getattr(self._subsystem, self.entity_description.attribute)
        if isinstance(value, IntEnum):
            return value.name.lower()
        return value
