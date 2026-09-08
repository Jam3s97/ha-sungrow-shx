"""End-to-end tests: does CONF_LEGACY_NAMING actually claim legacy entity ids."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sungrow.const import CONF_LEGACY_NAMING, DOMAIN

from .conftest import TCP_ENTRY_DATA
from .helpers import entity_id_for

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit


async def _setup_with_data(
    hass: HomeAssistant,
    data: dict[str, object],
    patch_async_get_unit: Callable[[MockModbusUnit], None],
    loaded_unit: MockModbusUnit,
) -> MockConfigEntry:
    patch_async_get_unit(loaded_unit)
    entry = MockConfigEntry(domain=DOMAIN, data=data, unique_id="tcp_10.0.0.5_1")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_legacy_naming_claims_flat_entity_ids(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    entry = await _setup_with_data(
        hass,
        {**TCP_ENTRY_DATA, CONF_LEGACY_NAMING: True},
        patch_async_get_unit,
        loaded_unit,
    )

    assert (
        entity_id_for(hass, entry, "sensor", "pv_mppt1_voltage")
        == "sensor.mppt1_voltage"
    )
    assert (
        entity_id_for(hass, entry, "switch", "controls_backup_mode_enabled")
        == "switch.backup_mode"
    )


async def test_modern_naming_is_still_the_default(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    entry = await _setup_with_data(
        hass, TCP_ENTRY_DATA, patch_async_get_unit, loaded_unit
    )

    entity_id = entity_id_for(hass, entry, "sensor", "pv_mppt1_voltage")
    assert entity_id != "sensor.mppt1_voltage"
    assert entity_id.endswith("_mppt1_voltage")
