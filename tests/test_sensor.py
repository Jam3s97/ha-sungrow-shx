"""Tests for the sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import entity_id_for, entity_id_missing

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_numeric_field_is_a_sensor(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "sensor", "pv_mppt1_voltage")
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 350.0


async def test_enum_field_reports_the_lowercase_option_key(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "sensor", "status_running_state")
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "running"


async def test_read_only_override_is_exposed_as_a_sensor_not_a_number(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    key = "controls_active_power_limitation_enabled"
    entity_id_for(hass, setup_integration, "sensor", key)
    assert entity_id_missing(hass, setup_integration, "number", key)
