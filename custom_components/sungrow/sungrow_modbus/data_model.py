"""Sungrow-specific pieces layered on the ``modbus_connection.model`` framework."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from modbus_connection.model import (
    Component,
    coil as _modbus_coil,
    enum as _modbus_enum,
    gauge as _modbus_gauge,
    int32 as _modbus_int32,
    string as _modbus_string,
    uint32 as _modbus_uint32,
)

from .metadata import (
    BooleanMetadata,
    DatapointMetadata,
    EnumMetadata,
    NumberMetadata,
    OptionMetadata,
    attach_metadata,
)

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit


class SungrowComponent(Component):
    """A Sungrow SHx sub-system: a group of related registers.

    A single Sungrow inverter answers reads over two distinct register
    spaces: the (mostly read-only) input registers documented as ``input``
    in Sungrow's register map, and the read/write holding registers used for
    settings and control. ``modbus-connection`` ties one ``Component`` to a
    single register space, so subsystems in this library are always either
    an input-register telemetry component or a holding-register control
    component -- never both. See :mod:`sungrow_modbus.subsystems` for the
    concrete split.
    """

    max_span = 100  # Sungrow answers wide block reads without complaint.

    def metadata_for(self, field: str) -> DatapointMetadata | None:
        """Return neutral Sungrow metadata for a declared field."""
        descriptor = type(self).declared_fields.get(field)
        if descriptor is None:
            return None
        return getattr(descriptor, "sungrow_metadata", None)

    def require_metadata_for(self, field: str) -> DatapointMetadata:
        """Return Sungrow metadata for a field or raise."""
        metadata = self.metadata_for(field)
        if metadata is None:
            raise AttributeError(f"unknown or untyped Sungrow field {field!r}")
        return metadata


def uint16(
    address: int,
    *,
    scale: float = 1.0,
    unit: str | None = None,
    min_value: float | int | None = None,
    max_value: float | int | None = None,
    step: float | int | None = None,
    nan: int | None = None,
    category: str | None = None,
    description: str | None = None,
    writable: bool = False,
):
    """An unsigned 16-bit register, optionally scaled."""
    field = _modbus_gauge(
        address,
        scale,
        signed=False,
        nan=nan,
        unit=unit,
        writable=writable,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            register_number=address + 1,
            category=category,
            description=description,
            writable=writable,
            number=NumberMetadata(
                min_value=min_value, max_value=max_value, step=step, unit=unit
            ),
        ),
    )


def int16(
    address: int,
    *,
    scale: float = 1.0,
    unit: str | None = None,
    min_value: float | int | None = None,
    max_value: float | int | None = None,
    step: float | int | None = None,
    nan: int | None = None,
    category: str | None = None,
    description: str | None = None,
    writable: bool = False,
):
    """A signed 16-bit register, optionally scaled."""
    field = _modbus_gauge(
        address,
        scale,
        signed=True,
        nan=nan,
        unit=unit,
        writable=writable,
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            register_number=address + 1,
            category=category,
            description=description,
            writable=writable,
            number=NumberMetadata(
                min_value=min_value, max_value=max_value, step=step, unit=unit
            ),
        ),
    )


def uint32_word_swapped(
    address: int,
    *,
    scale: float = 1.0,
    unit: str | None = None,
    nan: int | None = None,
    category: str | None = None,
    description: str | None = None,
):
    """An unsigned 32-bit value over two registers, low word first.

    Sungrow (like most SunSpec-flavoured inverters) stores 32-bit values with
    the low-order word at the lower address -- this is the ``swap: word``
    convention in the source ``modbus_sungrow.yaml``.
    """
    field = _modbus_uint32(
        address, scale=scale, word_order="little", nan=nan, unit=unit
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            register_number=address + 1,
            category=category,
            description=description,
            number=NumberMetadata(unit=unit),
        ),
    )


def int32_word_swapped(
    address: int,
    *,
    scale: float = 1.0,
    unit: str | None = None,
    nan: int | None = None,
    category: str | None = None,
    description: str | None = None,
):
    """A signed 32-bit value over two registers, low word first (see above)."""
    field = _modbus_int32(address, scale=scale, word_order="little", nan=nan, unit=unit)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="number",
            register_number=address + 1,
            category=category,
            description=description,
            number=NumberMetadata(unit=unit),
        ),
    )


def ascii_string(
    address: int,
    length: int,
    *,
    category: str | None = None,
    description: str | None = None,
):
    """A fixed-length ASCII string field."""
    field = _modbus_string(address, length)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="string",
            register_number=address + 1,
            category=category,
            description=description,
        ),
    )


def raw_enum(
    address: int,
    enum_type: type[IntEnum],
    *,
    category: str | None = None,
    description: str | None = None,
    writable: bool = False,
):
    """A register mapped to an ``IntEnum``, with options derived from it."""
    field = _modbus_enum(address, enum_type, writable=writable)
    options = tuple(
        OptionMetadata(member.name.lower(), int(member), member.name)
        for member in enum_type
    )
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="enum",
            register_number=address + 1,
            category=category,
            description=description,
            writable=writable,
            enum=EnumMetadata(enum_type=enum_type, options=options),
        ),
    )


def onoff_switch(
    address: int,
    *,
    category: str | None = None,
    description: str | None = None,
):
    """A holding register using Sungrow's 0xAA (on) / 0x55 (off) convention."""
    from .enums import OnOffCode

    field = _modbus_enum(address, OnOffCode, writable=True)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="boolean",
            register_number=address + 1,
            category=category,
            description=description,
            writable=True,
            boolean=BooleanMetadata(),
        ),
    )


def coil(address: int, *, writable: bool = False, category: str | None = None):
    """A coil (FC01/FC05)."""
    field = _modbus_coil(address, writable=writable)
    return attach_metadata(
        field,
        DatapointMetadata(
            value_kind="boolean",
            category=category,
            writable=writable,
            boolean=BooleanMetadata(),
        ),
    )


async def async_start_inverter(unit: ModbusUnit) -> None:
    """Send the start command to protocol address 12999 (register 13000)."""
    from .enums import InverterControlCommand

    await unit.write_register(12999, int(InverterControlCommand.START))


async def async_stop_inverter(unit: ModbusUnit) -> None:
    """Send the stop command to protocol address 12999 (register 13000)."""
    from .enums import InverterControlCommand

    await unit.write_register(12999, int(InverterControlCommand.STOP))
