"""Inverter AC output, temperature and running status."""

from __future__ import annotations

from ..data_model import SungrowComponent, int16, int32_word_swapped, raw_enum, uint16
from ..enums import RunningStateCode


class InverterStatus(SungrowComponent):
    """AC-side telemetry and operating status (input registers)."""

    register_space = "input"

    temperature = int16(5007, scale=0.1, unit="\u00b0C", category="inverter")
    phase_a_voltage = uint16(5018, scale=0.1, unit="V", category="inverter")
    phase_b_voltage = uint16(5019, scale=0.1, unit="V", category="inverter")
    phase_c_voltage = uint16(5020, scale=0.1, unit="V", category="inverter")
    reactive_power = int32_word_swapped(5032, unit="var", category="inverter")
    power_factor = int16(5034, scale=0.001, category="inverter")

    phase_a_current = int16(13030, scale=0.1, unit="A", category="inverter")
    phase_b_current = int16(13031, scale=0.1, unit="A", category="inverter")
    phase_c_current = int16(13032, scale=0.1, unit="A", category="inverter")
    total_active_power = int32_word_swapped(
        13033,
        unit="W",
        category="inverter",
        description="Total inverter AC output power.",
    )

    running_state = raw_enum(
        12999,
        RunningStateCode,
        category="inverter",
        description="Current operating state code.",
    )
    power_flow_status_raw = uint16(
        13000,
        category="inverter",
        description="Raw power-flow status bitmask (undocumented by Sungrow; "
        "exposed as-is for diagnostics).",
    )

    def _phase_power(
        self, voltage: float | None, current: float | None
    ) -> float | None:
        if voltage is None or current is None:
            return None
        return round(voltage * current)

    @property
    def phase_a_power(self) -> float | None:
        """Computed phase A power (V x I)."""
        return self._phase_power(self.phase_a_voltage, self.phase_a_current)

    @property
    def phase_b_power(self) -> float | None:
        """Computed phase B power (V x I)."""
        return self._phase_power(self.phase_b_voltage, self.phase_b_current)

    @property
    def phase_c_power(self) -> float | None:
        """Computed phase C power (V x I)."""
        return self._phase_power(self.phase_c_voltage, self.phase_c_current)

    @property
    def is_running(self) -> bool | None:
        """Whether the inverter reports a normal running state."""
        state = self.running_state
        if state is None:
            return None
        return state in (
            RunningStateCode.RUNNING,
            RunningStateCode.RUNNING_2,
            RunningStateCode.RUNNING_OFF_GRID,
            RunningStateCode.RUNNING_IN_MAINTAIN_MODE,
            RunningStateCode.RUNNING_IN_COMPULSORY_FORCED_MODE,
            RunningStateCode.RUNNING_IN_EXTERNAL_EMS_MODE,
        )
