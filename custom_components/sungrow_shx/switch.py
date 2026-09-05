"""Switch platform: every writable boolean (0xAA/0x55-style) field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .entity import SungrowEntity
from .field_index import FieldRef, iter_fields
from .sungrow_modbus import OnOffCode
from .unit_mapping import entity_category_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry


@dataclass(frozen=True, kw_only=True)
class SungrowSwitchDescription(SwitchEntityDescription):
    """Describes a writable boolean field on one component."""

    component: str
    attribute: str


def _description_for(field: FieldRef) -> SungrowSwitchDescription:
    return SungrowSwitchDescription(
        key=field.key,
        translation_key=field.key,
        name=field.name,
        component=field.component,
        attribute=field.attribute,
        entity_category=entity_category_for(field),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow SHx switches: every writable boolean field."""
    coordinator = entry.runtime_data
    descriptions = [
        _description_for(field)
        for field in iter_fields(coordinator.device)
        if field.is_writable and field.metadata.value_kind == "boolean"
    ]
    async_add_entities(SungrowSwitch(coordinator, d) for d in descriptions)


class SungrowSwitch(SungrowEntity, SwitchEntity):
    """A writable on/off setting."""

    entity_description: SungrowSwitchDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return whether the setting is currently enabled."""
        value = getattr(self._subsystem, self.entity_description.attribute)
        if value is None:
            return None
        return value is OnOffCode.ON

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable the setting."""
        await self._subsystem.write(self.entity_description.attribute, OnOffCode.ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable the setting."""
        await self._subsystem.write(self.entity_description.attribute, OnOffCode.OFF)
        await self.coordinator.async_request_refresh()
