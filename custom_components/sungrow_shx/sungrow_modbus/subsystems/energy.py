"""Daily and lifetime energy counters."""

from __future__ import annotations

from ..data_model import SungrowComponent, uint16, uint32_word_swapped


class EnergyTotals(SungrowComponent):
    """Daily/total energy counters (input registers, kWh unless noted)."""

    register_space = "input"

    daily_pv_generation_and_battery_discharge = uint16(
        5002,
        scale=0.1,
        unit="kWh",
        category="energy",
        description="Combined daily PV generation + battery discharge to load/grid.",
    )
    total_pv_generation_and_battery_discharge = uint32_word_swapped(
        5003, scale=0.1, unit="kWh", category="energy"
    )

    daily_pv_generation = uint16(13001, scale=0.1, unit="kWh", category="energy")
    total_pv_generation = uint32_word_swapped(
        13002, scale=0.1, unit="kWh", category="energy"
    )

    daily_exported_energy_from_pv = uint16(
        13004, scale=0.1, unit="kWh", category="energy"
    )
    total_exported_energy_from_pv = uint32_word_swapped(
        13005, scale=0.1, unit="kWh", category="energy"
    )

    daily_battery_charge_from_pv = uint16(
        13011, scale=0.1, unit="kWh", category="energy"
    )
    total_battery_charge_from_pv = uint32_word_swapped(
        13012, scale=0.1, unit="kWh", category="energy"
    )

    daily_direct_energy_consumption = uint16(
        13016, scale=0.1, unit="kWh", category="energy"
    )
    total_direct_energy_consumption = uint32_word_swapped(
        13017, scale=0.1, unit="kWh", category="energy"
    )

    daily_battery_discharge = uint16(13025, scale=0.1, unit="kWh", category="energy")
    total_battery_discharge = uint32_word_swapped(
        13026, scale=0.1, unit="kWh", category="energy"
    )

    daily_imported_energy = uint16(13035, scale=0.1, unit="kWh", category="energy")
    total_imported_energy = uint32_word_swapped(
        13036, scale=0.1, unit="kWh", category="energy"
    )

    daily_battery_charge = uint16(13039, scale=0.1, unit="kWh", category="energy")
    total_battery_charge = uint32_word_swapped(
        13040, scale=0.1, unit="kWh", category="energy"
    )

    daily_exported_energy = uint16(
        13044, scale=0.1, unit="kWh", nan=65535, category="energy"
    )
    total_exported_energy = uint32_word_swapped(
        13045, scale=0.1, unit="kWh", category="energy"
    )

    @property
    def daily_consumed_energy(self) -> float | None:
        """Daily household consumption, derived from the daily energy counters.

        ``pv_generation - exported + imported - battery_charge + battery_discharge``
        """
        parts = (
            self.daily_pv_generation,
            self.daily_exported_energy,
            self.daily_imported_energy,
            self.daily_battery_charge,
            self.daily_battery_discharge,
        )
        if any(part is None for part in parts):
            return None
        pv, exported, imported, charge, discharge = parts
        return round(pv - exported + imported - charge + discharge, 2)

    @property
    def total_consumed_energy(self) -> float | None:
        """Lifetime household consumption, derived the same way as the daily figure."""
        parts = (
            self.total_pv_generation,
            self.total_exported_energy,
            self.total_imported_energy,
            self.total_battery_charge,
            self.total_battery_discharge,
        )
        if any(part is None for part in parts):
            return None
        pv, exported, imported, charge, discharge = parts
        return round(pv - exported + imported - charge + discharge, 2)
