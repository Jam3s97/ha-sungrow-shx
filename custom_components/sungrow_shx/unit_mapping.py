"""Map a field's unit (and a few name hints) to Home Assistant sensor metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
    UnitOfTemperature,
)

if TYPE_CHECKING:
    from .field_index import FieldRef

_UNIT_MAP: dict[str, tuple[str, SensorDeviceClass | None]] = {
    "W": (UnitOfPower.WATT, SensorDeviceClass.POWER),
    "var": (UnitOfReactivePower.VOLT_AMPERE_REACTIVE, SensorDeviceClass.REACTIVE_POWER),
    "V": (UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
    "A": (UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
    "Hz": (UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY),
    "\u00b0C": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "kWh": (UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY),
}


def native_unit_and_device_class(
    field: FieldRef,
) -> tuple[str | None, SensorDeviceClass | None]:
    """Return (native_unit_of_measurement, device_class) for a numeric field."""
    unit = field.metadata.number.unit if field.metadata.number else None
    if unit is None:
        if (
            field.attribute.endswith(("_soc", "level", "soc"))
            or "soc" in field.attribute
        ):
            return PERCENTAGE, SensorDeviceClass.BATTERY
        return None, None
    if unit == "%":
        return PERCENTAGE, (
            SensorDeviceClass.BATTERY
            if "soc" in field.attribute or field.attribute == "level"
            else None
        )
    mapped = _UNIT_MAP.get(unit)
    if mapped is None:
        return unit, None
    return mapped


def state_class_for(field: FieldRef) -> SensorStateClass | None:
    """Return the appropriate state class, if any, for a numeric field."""
    unit = field.metadata.number.unit if field.metadata.number else None
    if unit == "kWh":
        return (
            SensorStateClass.TOTAL_INCREASING
            if field.attribute.startswith("total_")
            else SensorStateClass.TOTAL
        )
    if unit in (None, "kWh"):
        return None
    return SensorStateClass.MEASUREMENT


def entity_category_for(field: FieldRef) -> EntityCategory | None:
    """
    Return the entity category for a field.

    Config for writable controls, diagnostic for identity/raw/status fields,
    and unset (a normal primary entity) for everything else.
    """
    if field.is_writable:
        return EntityCategory.CONFIG
    if field.component == "info" or field.metadata.category == "identity":
        return EntityCategory.DIAGNOSTIC
    if field.attribute.endswith("_raw") or field.attribute in (
        "power_factor",
        "reactive_power",
    ):
        return EntityCategory.DIAGNOSTIC
    return None
