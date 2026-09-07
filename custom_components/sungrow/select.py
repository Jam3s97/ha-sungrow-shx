"""Select platform: every writable enum field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription

from .entity import SungrowEntity
from .field_index import FieldRef, iter_fields
from .unit_mapping import entity_category_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import SungrowDataUpdateCoordinator
    from .data import SungrowConfigEntry


@dataclass(frozen=True, kw_only=True)
class SungrowSelectDescription(SelectEntityDescription):
    """Describes a writable enum field on one component."""

    component: str
    attribute: str
    enum_type: type


def _description_for(field: FieldRef) -> SungrowSelectDescription:
    options = [option.key for option in field.metadata.enum.options]
    return SungrowSelectDescription(
        key=field.key,
        translation_key=field.key,
        name=field.name,
        component=field.component,
        attribute=field.attribute,
        enum_type=field.metadata.enum.enum_type,
        options=options,
        entity_category=entity_category_for(field),
    )


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: SungrowConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Sungrow selects: every writable enum field."""
    coordinator = entry.runtime_data
    descriptions = [
        _description_for(field)
        for field in iter_fields(coordinator.device)
        if field.is_writable and field.metadata.value_kind == "enum"
    ]
    async_add_entities(SungrowSelect(coordinator, d) for d in descriptions)


class SungrowSelect(SungrowEntity, SelectEntity):
    """A writable enum setting."""

    entity_description: SungrowSelectDescription

    def __init__(
        self,
        coordinator: SungrowDataUpdateCoordinator,
        description: SungrowSelectDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, description.key, description.component)
        self.entity_description = description

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option's key."""
        value = getattr(self._subsystem, self.entity_description.attribute)
        return value.name.lower() if value is not None else None

    async def async_select_option(self, option: str) -> None:
        """Write the chosen option to the inverter."""
        member = self.entity_description.enum_type[option.upper()]
        await self._subsystem.write(self.entity_description.attribute, member)
        await self.coordinator.async_request_refresh()
