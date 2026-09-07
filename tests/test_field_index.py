"""Tests for ``field_index.py``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sungrow.field_index import FieldRef, iter_fields
from custom_components.sungrow.sungrow_modbus.metadata import DatapointMetadata

if TYPE_CHECKING:
    from custom_components.sungrow.sungrow_modbus import SungrowSHx

_NUMBER = DatapointMetadata(value_kind="number")


def test_key_is_component_and_attribute() -> None:
    field = FieldRef("pv", "mppt1_voltage", _NUMBER)
    assert field.key == "pv_mppt1_voltage"


def test_name_uppercases_mppt_prefix() -> None:
    assert FieldRef("pv", "mppt1_voltage", _NUMBER).name == "MPPT1 voltage"


def test_name_uppercases_known_acronyms() -> None:
    assert (
        FieldRef("energy", "daily_pv_generation", _NUMBER).name == "Daily PV generation"
    )
    assert (
        FieldRef("battery", "bms_max_charging_current", _NUMBER).name
        == "BMS max charging current"
    )


def test_name_capitalizes_plain_words() -> None:
    assert FieldRef("battery", "state_of_health", _NUMBER).name == "State of health"


def test_is_writable_follows_metadata_by_default() -> None:
    writable = DatapointMetadata(value_kind="number", writable=True)
    read_only = DatapointMetadata(value_kind="number", writable=False)
    assert FieldRef("controls", "export_power_limit", writable).is_writable
    assert not FieldRef("controls", "some_field", read_only).is_writable


def test_is_writable_override_forces_read_only() -> None:
    writable = DatapointMetadata(value_kind="number", writable=True)
    field = FieldRef("controls", "active_power_limitation_enabled", writable)
    assert not field.is_writable


async def test_iter_fields_yields_declared_fields(device: SungrowSHx) -> None:
    keys = {field.key for field in iter_fields(device)}
    assert "pv_mppt1_voltage" in keys
    assert "controls_export_power_limit" in keys
    assert "battery_settings_max_soc" in keys


async def test_iter_fields_skips_internal_underscore_attributes(
    device: SungrowSHx,
) -> None:
    fields = list(iter_fields(device))
    assert not any(field.attribute.startswith("_") for field in fields)
    assert not any(field.key == "info__version_part_1" for field in fields)
