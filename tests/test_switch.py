"""Tests for the switch platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import entity_id_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_writable_boolean_reads_off(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    entity_id = entity_id_for(
        hass, setup_integration, "switch", "controls_backup_mode_enabled"
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"


async def test_turn_on_writes_through_to_the_inverter(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(
        hass, setup_integration, "switch", "controls_backup_mode_enabled"
    )

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[13074] == 0xAA
    assert hass.states.get(entity_id).state == "on"


async def test_turn_off_writes_through_to_the_inverter(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(
        hass, setup_integration, "switch", "controls_backup_mode_enabled"
    )

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[13074] == 0x55
    assert hass.states.get(entity_id).state == "off"
