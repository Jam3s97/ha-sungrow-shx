"""
Shared fixtures for the Sungrow integration test suite.

Every test talks to a ``SungrowSHx`` over ``modbus_connection``'s in-memory
mock backend (``mock_modbus_unit``, from the ``modbus_connection`` pytest
plugin, auto-registered as a dependency) -- never a real socket. ``async_get_unit``
and ``async_get_temporary_unit`` (Home Assistant core's Modbus connection
pool, see custom_components/sungrow/__init__.py and config_flow.py) are
patched to hand out that same mock unit instead of opening one.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sungrow.const import (
    CONF_MODBUS_TYPE,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MODBUS_TYPE_TCP,
)
from custom_components.sungrow.sungrow_modbus import SungrowSHx

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit

TCP_ENTRY_DATA: dict[str, Any] = {
    CONF_MODBUS_TYPE: MODBUS_TYPE_TCP,
    CONF_HOST: "10.0.0.5",
    CONF_PORT: DEFAULT_PORT,
    CONF_UNIT_ID: DEFAULT_UNIT_ID,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Make ``custom_components.sungrow`` loadable by every test's ``hass``."""


def _split_word_swapped(value: int) -> tuple[int, int]:
    """Split a signed/unsigned 32-bit value into (low_word, high_word)."""
    raw = value & 0xFFFFFFFF
    return raw & 0xFFFF, (raw >> 16) & 0xFFFF


# A realistic register snapshot: one value per field actually exercised by
# the test suite. Addresses are protocol addresses, matching what
# ``MockModbusUnit`` (and a real inverter) is read/written at.
INPUT: dict[int, int] = {
    4999: 0x0E03,  # device_type_code_raw -> SH10RT
    5000: 100,  # rated_output_power -> 10000 W (scale 100)
    5010: 3500,  # mppt1_voltage -> 350.0 V
    5011: 82,  # mppt1_current -> 8.2 A
    5016: _split_word_swapped(4500)[0],  # total_dc_power (uint32, word-swapped)
    5017: _split_word_swapped(4500)[1],  # -> 4500 W
    12999: 0x0000,  # running_state -> RUNNING
    13019: 4850,  # battery voltage -> 485.0 V
    13022: 550,  # battery level -> 55.0 %
    13023: 993,  # battery state_of_health -> 99.3 %
    5213: _split_word_swapped(-1500)[0],  # battery power (int32, word-swapped)
    5214: _split_word_swapped(-1500)[1],  # -> -1500 W (charging)
    5241: 5001,  # grid frequency -> 50.01 Hz
    13009: _split_word_swapped(-300)[0],  # export_power_raw (int32, word-swapped)
    13010: _split_word_swapped(-300)[1],  # -> -300 W (importing)
    13001: 125,  # daily_pv_generation -> 12.5 kWh
}

HOLDING: dict[int, int] = {
    13049: 0,  # ems_mode -> SELF_CONSUMPTION
    13073: 5000,  # export_power_limit -> 5000 W
    13074: 0x55,  # backup_mode_enabled -> OFF
    13057: 900,  # battery max_soc -> 90.0 %
    13058: 100,  # battery min_soc -> 10.0 %
}


@pytest.fixture
def loaded_unit(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    """Return a mock Modbus unit pre-loaded with a realistic Sungrow SHx snapshot."""
    mock_modbus_unit.input.update(INPUT)
    mock_modbus_unit.holding.update(HOLDING)
    return mock_modbus_unit


@pytest.fixture
async def device(loaded_unit: MockModbusUnit) -> SungrowSHx:
    """Return a ``SungrowSHx`` that has already performed one ``async_update``."""
    dev = SungrowSHx(loaded_unit)
    await dev.async_update()
    return dev


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a TCP config entry for the inverter described by ``loaded_unit``."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=TCP_ENTRY_DATA,
        unique_id="tcp_10.0.0.5_1",
        title="SH10RT",
    )


@pytest.fixture
def patch_async_get_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[MockModbusUnit | Exception], None]:
    """Patch ``__init__.py``'s ``async_get_unit`` to hand out (or fail with) a unit."""

    def _patch(unit_or_error: MockModbusUnit | Exception) -> None:
        def _fake(hass: object, entry: object, params: object, unit_id: int) -> object:
            if isinstance(unit_or_error, Exception):
                raise unit_or_error
            return unit_or_error

        monkeypatch.setattr("custom_components.sungrow.async_get_unit", _fake)

    return _patch


@pytest.fixture
def patch_async_get_temporary_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[MockModbusUnit | Exception], None]:
    """Patch ``config_flow.py``'s ``async_get_temporary_unit`` the same way."""

    def _patch(unit_or_error: MockModbusUnit | Exception) -> None:
        @asynccontextmanager
        async def _fake(
            hass: object, params: object, unit_id: int
        ) -> Iterator[MockModbusUnit]:
            if isinstance(unit_or_error, Exception):
                raise unit_or_error
            yield unit_or_error

        monkeypatch.setattr(
            "custom_components.sungrow.config_flow.async_get_temporary_unit", _fake
        )

    return _patch


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    patch_async_get_unit: Callable[[MockModbusUnit | Exception], None],
    loaded_unit: MockModbusUnit,
) -> MockConfigEntry:
    """Fully set up the Sungrow integration against ``loaded_unit``."""
    patch_async_get_unit(loaded_unit)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
