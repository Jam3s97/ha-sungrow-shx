"""Battery telemetry and battery-related settings.

Split into two components because they live in different Modbus register
spaces: :class:`BatteryTelemetry` reads input registers, :class:`BatterySettings`
reads/writes holding registers.
"""

from __future__ import annotations

from ..data_model import (
    SungrowComponent,
    int16,
    int32_word_swapped,
    raw_enum,
    uint16,
)
from ..enums import ForcedChargeDischargeCommand


class BatteryTelemetry(SungrowComponent):
    """Battery measurements (input registers)."""

    register_space = "input"

    power = int32_word_swapped(
        5213,
        unit="W",
        category="battery",
        description="Battery power; negative while charging, positive while\n"
        "discharging.",
    )
    current = int16(5630, scale=0.1, unit="A", category="battery")
    bms_max_charging_current = uint16(5634, unit="A", category="battery")
    bms_max_discharging_current = uint16(5635, unit="A", category="battery")
    bdc_rated_power = uint16(5627, scale=100, unit="W", category="battery")
    capacity_high_precision = uint16(
        5638,
        scale=0.01,
        unit="kWh",
        category="battery",
        description="Rated battery capacity at high precision.",
    )
    voltage = uint16(13019, scale=0.1, unit="V", category="battery")
    level = uint16(
        13022,
        scale=0.1,
        unit="%",
        category="battery",
        description="Raw state of charge.",
    )
    state_of_health = uint16(13023, scale=0.1, unit="%", category="battery")
    temperature = int16(13024, scale=0.1, unit="\u00b0C", category="battery")

    @property
    def charging_power(self) -> float | None:
        """Charging power (W), 0 while idle or discharging."""
        if self.power is None:
            return None
        return max(-self.power, 0)

    @property
    def discharging_power(self) -> float | None:
        """Discharging power (W), 0 while idle or charging."""
        if self.power is None:
            return None
        return max(self.power, 0)

    @property
    def is_charging(self) -> bool | None:
        """Whether the battery is currently charging."""
        if self.power is None:
            return None
        return self.power < 0

    @property
    def is_discharging(self) -> bool | None:
        """Whether the battery is currently discharging."""
        if self.power is None:
            return None
        return self.power > 0

    def nominal_level(
        self, min_soc: float | None, max_soc: float | None
    ) -> float | None:
        """Battery level rescaled into the usable ``min_soc..max_soc`` band."""
        if self.level is None or min_soc is None or max_soc is None:
            return None
        return round(min_soc + (max_soc - min_soc) * (self.level / 100), 1)

    def usable_charge_kwh(
        self, min_soc: float | None, max_soc: float | None
    ) -> float | None:
        """Usable stored energy (kWh) within the configured SoC band."""
        if self.capacity_high_precision is None or self.level is None:
            return None
        if min_soc is None or max_soc is None:
            return None
        return round(
            self.capacity_high_precision * (max_soc - min_soc) / 100 * self.level / 100,
            2,
        )

    def health_rated_charge_kwh(
        self, min_soc: float | None, max_soc: float | None
    ) -> float | None:
        """Usable stored energy (kWh) further scaled by state of health."""
        charge = self.usable_charge_kwh(min_soc, max_soc)
        if charge is None or self.state_of_health is None:
            return None
        return round(charge * self.state_of_health / 100, 2)


class BatterySettings(SungrowComponent):
    """Battery-related settings and controls (holding registers)."""

    register_space = "holding"

    forced_charge_discharge_command = raw_enum(
        13050,
        ForcedChargeDischargeCommand,
        category="battery",
        description="Forced charge/discharge command.",
        writable=True,
    )
    forced_charge_discharge_power = uint16(
        13051,
        unit="W",
        category="battery",
        description="Power target used while a forced charge/discharge command "
        "is active.",
        writable=True,
    )
    max_soc = uint16(
        13057,
        scale=0.1,
        unit="%",
        min_value=50,
        max_value=100,
        category="battery",
        writable=True,
    )
    min_soc = uint16(
        13058,
        scale=0.1,
        unit="%",
        min_value=0,
        max_value=50,
        category="battery",
        writable=True,
    )
    reserved_soc_for_backup = uint16(
        13099,
        unit="%",
        min_value=0,
        max_value=100,
        category="battery",
        writable=True,
    )
    max_charge_power = uint16(
        33046,
        scale=10,
        unit="W",
        min_value=10,
        category="battery",
        writable=True,
    )
    max_discharge_power = uint16(
        33047,
        scale=10,
        unit="W",
        min_value=10,
        category="battery",
        writable=True,
    )
    charging_start_power = uint16(
        33148,
        scale=10,
        unit="W",
        min_value=0,
        max_value=1000,
        nan=65535,
        category="battery",
        writable=True,
    )
    discharging_start_power = uint16(
        33149,
        scale=10,
        unit="W",
        min_value=0,
        max_value=1000,
        nan=65535,
        category="battery",
        writable=True,
    )
