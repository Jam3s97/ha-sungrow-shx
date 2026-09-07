"""Tests for the button platform (inverter start/stop)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.helpers import entity_id_for

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_start_inverter_writes_the_start_command(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "button", "start_inverter")

    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[12999] == 0xCF


async def test_stop_inverter_writes_the_stop_command(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    loaded_unit: MockModbusUnit,
) -> None:
    entity_id = entity_id_for(hass, setup_integration, "button", "stop_inverter")

    await hass.services.async_call(
        "button", "press", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert loaded_unit.holding[12999] == 0xCE
