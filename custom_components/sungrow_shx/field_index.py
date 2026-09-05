"""
Turn ``sungrow_modbus`` field metadata into Home Assistant entity descriptions.

The device library attaches a :class:`~sungrow_modbus.metadata.DatapointMetadata`
to every declared register field (see ``sungrow_modbus.data_model``). Rather
than hand-listing every one of the ~100 registers again in each platform
module, every platform here iterates this same index and picks up whichever
fields match its ``value_kind``/``writable`` combination. Adding a field to
the library therefore surfaces it in Home Assistant automatically, with no
matching platform-side change required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .sungrow_modbus import SungrowSHx
    from .sungrow_modbus.metadata import DatapointMetadata

# (attribute name on SungrowSHx, whether its fields are read-only from HA's
# perspective even if the underlying subsystem is a holding-register one).
_COMPONENTS: tuple[str, ...] = (
    "info",
    "pv",
    "status",
    "battery",
    "battery_settings",
    "grid",
    "backup",
    "energy",
    "controls",
)

# Registers that are technically writable in the library but are exposed as
# read-only diagnostics in Home Assistant because writing them without also
# coordinating the paired field(s) below would be unsafe or meaningless.
_READ_ONLY_OVERRIDE: frozenset[tuple[str, str]] = frozenset(
    {
        # Reading this flag's real-world effect isn't documented; exposing a
        # raw number to flip blind is worse than leaving it diagnostic-only.
        ("controls", "active_power_limitation_enabled"),
    }
)


@dataclass(frozen=True)
class FieldRef:
    """One declared field, resolved to where it lives on the device."""

    component: str
    attribute: str
    metadata: DatapointMetadata

    @property
    def key(self) -> str:
        """Unique entity key: stable across restarts, one per field."""
        return f"{self.component}_{self.attribute}"

    @property
    def name(self) -> str:
        """
        A human name derived from the attribute.

        E.g. 'mppt1_voltage' -> 'MPPT1 voltage'.
        """
        words = self.attribute.split("_")
        out = []
        for word in words:
            if (
                word.lower().startswith("mppt") and word[4:].isdigit()
            ) or word.lower() in (
                "soc",
                "pv",
                "dc",
                "ac",
                "apl",
                "bms",
                "bdc",
                "ems",
                "arm",
                "dsp",
            ):
                out.append(word.upper())
            else:
                out.append(word)
        text = " ".join(out)
        return text[0].upper() + text[1:]

    @property
    def is_writable(self) -> bool:
        """Whether this field should be exposed as a control, not a sensor."""
        if (self.component, self.attribute) in _READ_ONLY_OVERRIDE:
            return False
        return self.metadata.writable


def iter_fields(device: SungrowSHx) -> Iterator[FieldRef]:
    """
    Yield every declared, Sungrow-metadata-tagged field on the device.

    Attributes starting with an underscore are internal building blocks for
    a computed property (see e.g. ``DeviceInformation.firmware_version``)
    and are deliberately not surfaced as their own entity.
    """
    for component_name in _COMPONENTS:
        component = getattr(device, component_name)
        declared = type(component).declared_fields
        for attribute in declared:
            if attribute.startswith("_"):
                continue
            metadata = getattr(declared[attribute], "sungrow_metadata", None)
            if metadata is None:
                continue
            yield FieldRef(component_name, attribute, metadata)
