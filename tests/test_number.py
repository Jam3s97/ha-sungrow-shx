"""Tests for the number platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import entity_id_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_writable_number_reads_its_current_value(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entity_id = entity_id_for(
        hass, setup_integration, "number", "controls_export_power_limit"
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 5000


async def test_set_native_value_writes_through_to_the_inverter(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(
        hass, setup_integration, "number", "controls_export_power_limit"
    )

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id, "value": 6000},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[13073] == 6000
    assert float(hass.states.get(entity_id).state) == 6000
