"""Tests for ``SungrowDataUpdateCoordinator``."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from modbus_connection import ModbusError

from custom_components.sungrow.coordinator import SungrowDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.sungrow.sungrow_modbus import SungrowSHx


async def test_update_data_returns_the_device_after_updating(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, device: SungrowSHx
) -> None:
    mock_config_entry.add_to_hass(hass)
    device.async_update = AsyncMock(wraps=device.async_update)
    coordinator = SungrowDataUpdateCoordinator(hass, mock_config_entry, device)

    result = await coordinator._async_update_data()  # noqa: SLF001

    device.async_update.assert_awaited_once()
    assert result is device


async def test_update_data_wraps_modbus_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, device: SungrowSHx
) -> None:
    mock_config_entry.add_to_hass(hass)
    device.async_update = AsyncMock(side_effect=ModbusError("unreachable"))
    coordinator = SungrowDataUpdateCoordinator(hass, mock_config_entry, device)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()  # noqa: SLF001
