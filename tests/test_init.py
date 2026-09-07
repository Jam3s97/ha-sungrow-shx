"""Tests for ``__init__.py``: setup and unload of a config entry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_entry_loads_and_populates_runtime_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    patch_async_get_unit: Callable[[MockModbusUnit], None],
    loaded_unit: MockModbusUnit,
) -> None:
    patch_async_get_unit(loaded_unit)
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data is not None
    assert mock_config_entry.runtime_data.device.info.model == "SH10RT"


async def test_setup_entry_not_ready_when_connection_cannot_be_claimed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    patch_async_get_unit: Callable[[Exception], None],
) -> None:
    patch_async_get_unit(HomeAssistantError("device already in use"))
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()

    assert setup_integration.state is ConfigEntryState.NOT_LOADED
