"""Grid connection point: meter readings and import/export power."""

from __future__ import annotations

from ..data_model import SungrowComponent, int16, int32_word_swapped, uint16


class GridMeter(SungrowComponent):
    """Grid meter telemetry (input registers)."""

    register_space = "input"

    frequency = uint16(5241, scale=0.01, unit="Hz", category="grid")

    meter_active_power = int32_word_swapped(
        5600,
        unit="W",
        nan=2147483647,
        category="grid",
        description="Signed grid meter power; positive is import, negative is export.",
    )
    meter_phase_a_active_power = int32_word_swapped(
        5602, unit="W", nan=2147483647, category="grid"
    )
    meter_phase_b_active_power = int32_word_swapped(
        5604, unit="W", nan=2147483647, category="grid"
    )
    meter_phase_c_active_power = int32_word_swapped(
        5606, unit="W", nan=2147483647, category="grid"
    )

    meter_phase_a_voltage = int16(5740, scale=0.1, unit="V", nan=32767, category="grid")
    meter_phase_b_voltage = int16(5741, scale=0.1, unit="V", nan=32767, category="grid")
    meter_phase_c_voltage = int16(5742, scale=0.1, unit="V", nan=32767, category="grid")
    meter_phase_a_current = uint16(
        5743, scale=0.01, unit="A", nan=65535, category="grid"
    )
    meter_phase_b_current = uint16(
        5744, scale=0.01, unit="A", nan=65535, category="grid"
    )
    meter_phase_c_current = uint16(
        5745, scale=0.01, unit="A", nan=65535, category="grid"
    )

    export_power_limit_min = uint16(
        5621,
        scale=10,
        unit="W",
        nan=65535,
        category="grid",
        description="Lower bound accepted for the export power limit setting.",
    )
    export_power_limit_max = uint16(
        5622,
        scale=10,
        unit="W",
        nan=65535,
        category="grid",
        description="Upper bound accepted for the export power limit setting.",
    )

    load_power = int32_word_swapped(
        13007,
        unit="W",
        nan=2147483647,
        category="grid",
        description="Total household load power.",
    )
    export_power_raw = int32_word_swapped(
        13009,
        unit="W",
        nan=2147483647,
        category="grid",
        description="Signed export power; positive is exporting, negative is\n"
        "importing.",
    )

    @property
    def import_power(self) -> float | None:
        """Power currently being imported from the grid (W), 0 while exporting."""
        if self.export_power_raw is None:
            return None
        return max(-self.export_power_raw, 0)

    @property
    def export_power(self) -> float | None:
        """Power currently being exported to the grid (W), 0 while importing."""
        if self.export_power_raw is None:
            return None
        return max(self.export_power_raw, 0)

    @property
    def is_importing(self) -> bool | None:
        """Whether the site is currently importing from the grid."""
        if self.export_power_raw is None:
            return None
        return self.export_power_raw < 0

    @property
    def is_exporting(self) -> bool | None:
        """Whether the site is currently exporting to the grid."""
        if self.export_power_raw is None:
            return None
        return self.export_power_raw > 0
