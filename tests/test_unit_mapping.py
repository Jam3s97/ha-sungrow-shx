"""Tests for ``unit_mapping.py``."""

from __future__ import annotations

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower

from custom_components.sungrow.field_index import FieldRef
from custom_components.sungrow.sungrow_modbus.metadata import (
    DatapointMetadata,
    NumberMetadata,
)
from custom_components.sungrow.unit_mapping import (
    entity_category_for,
    native_unit_and_device_class,
    state_class_for,
)


def _field(
    attribute: str,
    *,
    component: str = "pv",
    unit: str | None = None,
    writable: bool = False,
    category: str | None = None,
) -> FieldRef:
    metadata = DatapointMetadata(
        value_kind="number",
        writable=writable,
        category=category,
        number=NumberMetadata(unit=unit) if unit is not None else None,
    )
    return FieldRef(component, attribute, metadata)


@pytest.mark.parametrize(
    ("unit", "expected_unit", "expected_class"),
    [
        ("W", UnitOfPower.WATT, SensorDeviceClass.POWER),
        ("V", "V", SensorDeviceClass.VOLTAGE),
        ("A", "A", SensorDeviceClass.CURRENT),
        ("Hz", "Hz", SensorDeviceClass.FREQUENCY),
        ("kWh", "kWh", SensorDeviceClass.ENERGY),
    ],
)
def test_native_unit_and_device_class_known_units(
    unit: str, expected_unit: str, expected_class: SensorDeviceClass
) -> None:
    mapped_unit, device_class = native_unit_and_device_class(
        _field("mppt1_voltage", unit=unit)
    )
    assert mapped_unit == expected_unit
    assert device_class is expected_class


def test_native_unit_and_device_class_unknown_unit_passes_through() -> None:
    unit, device_class = native_unit_and_device_class(_field("something", unit="rpm"))
    assert unit == "rpm"
    assert device_class is None


def test_native_unit_and_device_class_percent_soc_is_battery() -> None:
    unit, device_class = native_unit_and_device_class(
        _field("level", component="battery", unit="%")
    )
    assert unit == PERCENTAGE
    assert device_class is SensorDeviceClass.BATTERY


def test_native_unit_and_device_class_percent_non_soc_has_no_class() -> None:
    unit, device_class = native_unit_and_device_class(
        _field("active_power_limitation_ratio", component="controls", unit="%")
    )
    assert unit == PERCENTAGE
    assert device_class is None


def test_native_unit_and_device_class_no_unit_but_soc_name() -> None:
    unit, device_class = native_unit_and_device_class(
        _field("battery_soc", component="battery")
    )
    assert unit == PERCENTAGE
    assert device_class is SensorDeviceClass.BATTERY


def test_native_unit_and_device_class_no_unit_no_hint() -> None:
    unit, device_class = native_unit_and_device_class(_field("serial_number"))
    assert unit is None
    assert device_class is None


def test_state_class_for_total_increasing_energy() -> None:
    """Daily counters reset to ~0 each day -- total_increasing handles that reset."""
    field = _field("daily_pv_generation", component="energy", unit="kWh")
    assert state_class_for(field) is SensorStateClass.TOTAL_INCREASING


def test_state_class_for_non_total_energy() -> None:
    """Lifetime counters only reset rarely (firmware/meter swap) -- plain total."""
    field = _field("total_pv_generation", component="energy", unit="kWh")
    assert state_class_for(field) is SensorStateClass.TOTAL


def test_state_class_for_measurement() -> None:
    field = _field("mppt1_voltage", unit="V")
    assert state_class_for(field) is SensorStateClass.MEASUREMENT


def test_state_class_for_no_unit_is_none() -> None:
    field = _field("serial_number")
    assert state_class_for(field) is None


def test_entity_category_for_writable_is_config() -> None:
    field = _field("export_power_limit", component="controls", writable=True)
    assert entity_category_for(field) is EntityCategory.CONFIG


def test_entity_category_for_identity_is_diagnostic() -> None:
    field = _field("serial_number", component="info")
    assert entity_category_for(field) is EntityCategory.DIAGNOSTIC


def test_entity_category_for_raw_suffix_is_diagnostic() -> None:
    field = _field("power_flow_status_raw", component="status")
    assert entity_category_for(field) is EntityCategory.DIAGNOSTIC


def test_entity_category_for_normal_field_is_none() -> None:
    field = _field("mppt1_voltage")
    assert entity_category_for(field) is None
