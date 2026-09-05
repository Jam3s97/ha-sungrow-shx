"""Neutral Sungrow datapoint metadata.

Mirrors the pattern used by other ``modbus-connection`` device libraries
(see trovis-modbus): every field declared through :mod:`sungrow_modbus.data_model`
carries a small, backend-neutral ``DatapointMetadata`` object describing what
it is, independent of any particular consumer (Home Assistant or otherwise).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Literal

ValueKind = Literal["number", "enum", "boolean", "raw", "string"]


@dataclass(frozen=True)
class NumberMetadata:
    """Metadata for numeric Sungrow values."""

    min_value: float | int | None = None
    max_value: float | int | None = None
    step: float | int | None = None
    unit: str | None = None


@dataclass(frozen=True)
class OptionMetadata:
    """Metadata for one discrete option of an enum-valued field."""

    key: str
    value: int
    label: str | None = None


@dataclass(frozen=True)
class EnumMetadata:
    """Metadata for selectable / discrete register values."""

    enum_type: type[IntEnum]
    options: tuple[OptionMetadata, ...]


@dataclass(frozen=True)
class BooleanMetadata:
    """Metadata for boolean-like register values (e.g. 0xAA/0x55 switches)."""

    false_key: str = "off"
    true_key: str = "on"


@dataclass(frozen=True)
class DatapointMetadata:
    """Neutral metadata for one Sungrow datapoint."""

    value_kind: ValueKind
    register_number: int | None = None
    category: str | None = None
    description: str | None = None
    writable: bool = False
    number: NumberMetadata | None = None
    enum: EnumMetadata | None = None
    boolean: BooleanMetadata | None = None


def attach_metadata(field: Any, metadata: DatapointMetadata) -> Any:
    """Attach Sungrow metadata to a modbus-connection field."""
    field.sungrow_metadata = metadata
    return field
