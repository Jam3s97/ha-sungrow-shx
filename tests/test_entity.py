"""Tests for the ``SungrowEntity`` base class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sungrow.coordinator import SungrowDataUpdateCoordinator
from custom_components.sungrow.entity import SungrowEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.sungrow.sungrow_modbus import SungrowSHx


async def test_entity_identity_and_device_info(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, device: SungrowSHx
) -> None:
    mock_config_entry.add_to_hass(hass)
    coordinator = SungrowDataUpdateCoordinator(hass, mock_config_entry, device)
    entity = SungrowEntity(coordinator, "pv_mppt1_voltage", "pv", "sensor")

    assert entity.unique_id == f"{mock_config_entry.entry_id}_pv_mppt1_voltage"
    assert entity._subsystem is device.pv  # noqa: SLF001

    info = entity.device_info
    assert info is not None
    assert info["manufacturer"] == "Sungrow"
    assert info["model"] == "SH10RT"
    assert info["serial_number"] == device.info.serial_number
    assert info["identifiers"] == {("sungrow", mock_config_entry.entry_id)}
