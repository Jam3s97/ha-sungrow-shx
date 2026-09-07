"""Tests for the binary sensor platform (computed, multi-component flags)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.helpers import entity_id_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.parametrize(
    "key",
    ["is_pv_generating", "is_battery_charging", "is_importing_from_grid", "is_running"],
)
async def test_computed_flags_are_on(
    hass: HomeAssistant, setup_integration: MockConfigEntry, key: str
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "binary_sensor", key)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "on"
