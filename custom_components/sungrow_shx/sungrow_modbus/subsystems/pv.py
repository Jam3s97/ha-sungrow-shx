"""PV string (MPPT) telemetry."""

from __future__ import annotations

from ..data_model import SungrowComponent, uint16, uint32_word_swapped


class PVStrings(SungrowComponent):
    """Per-MPPT voltage/current and total DC power (input registers)."""

    register_space = "input"

    mppt1_voltage = uint16(5010, scale=0.1, unit="V", category="pv")
    mppt1_current = uint16(5011, scale=0.1, unit="A", category="pv")
    mppt2_voltage = uint16(5012, scale=0.1, unit="V", category="pv")
    mppt2_current = uint16(5013, scale=0.1, unit="A", category="pv")
    mppt3_voltage = uint16(5014, scale=0.1, unit="V", nan=65535, category="pv")
    mppt3_current = uint16(5015, scale=0.1, unit="A", nan=65535, category="pv")
    mppt4_voltage = uint16(5114, scale=0.1, unit="V", nan=65535, category="pv")
    mppt4_current = uint16(5115, scale=0.1, unit="A", nan=65535, category="pv")
    total_dc_power = uint32_word_swapped(
        5016, unit="W", category="pv", description="Sum of all MPPT string power."
    )

    def _string_power(
        self, voltage: float | None, current: float | None
    ) -> float | None:
        if voltage is None or current is None:
            return None
        return round(voltage * current)

    @property
    def mppt1_power(self) -> float | None:
        """Computed MPPT1 power (V x I); Sungrow has no dedicated register for it."""
        return self._string_power(self.mppt1_voltage, self.mppt1_current)

    @property
    def mppt2_power(self) -> float | None:
        """Computed MPPT2 power (V x I)."""
        return self._string_power(self.mppt2_voltage, self.mppt2_current)

    @property
    def mppt3_power(self) -> float | None:
        """Computed MPPT3 power (V x I)."""
        return self._string_power(self.mppt3_voltage, self.mppt3_current)

    @property
    def mppt4_power(self) -> float | None:
        """Computed MPPT4 power (V x I)."""
        return self._string_power(self.mppt4_voltage, self.mppt4_current)

    @property
    def is_generating(self) -> bool | None:
        """Whether any PV string is currently producing power."""
        if self.total_dc_power is None:
            return None
        return self.total_dc_power > 0
