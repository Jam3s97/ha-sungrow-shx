"""Tests for the select platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import entity_id_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_writable_enum_reads_its_current_option(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "select", "controls_ems_mode")
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "self_consumption"


async def test_select_option_writes_through_to_the_inverter(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "select", "controls_ems_mode")

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id, "option": "forced_mode"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[13049] == 2
    assert hass.states.get(entity_id).state == "forced_mode"
