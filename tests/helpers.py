"""Shared helpers for the Sungrow test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import entity_registry as er

from custom_components.sungrow.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


def entity_id_for(
    hass: HomeAssistant, entry: MockConfigEntry, platform: str, key: str
) -> str:
    """Look up the entity_id the registry assigned for one field's key."""
    registry = er.async_get(hass)
    unique_id = f"{entry.entry_id}_{key}"
    entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None, f"no {platform} entity registered for {unique_id!r}"
    return entity_id


def entity_id_missing(
    hass: HomeAssistant, entry: MockConfigEntry, platform: str, key: str
) -> bool:
    """Whether no entity of ``platform`` was registered for this field's key."""
    registry = er.async_get(hass)
    unique_id = f"{entry.entry_id}_{key}"
    return registry.async_get_entity_id(platform, DOMAIN, unique_id) is None
