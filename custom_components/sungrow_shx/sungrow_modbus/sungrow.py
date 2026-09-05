"""The top-level Sungrow SHx device object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from modbus_connection.model import Component, ComponentGroup

from .data_model import async_start_inverter, async_stop_inverter
from .device_info import DeviceInformation
from .subsystems import (
    BackupPower,
    BatterySettings,
    BatteryTelemetry,
    Controls,
    EnergyTotals,
    GridMeter,
    InverterStatus,
    PVStrings,
)

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit


class SungrowSHx:
    """A Sungrow SHx hybrid inverter.

    Owns one :class:`~modbus_connection.model.Component` per subsystem and
    pools their reads through a single :class:`ComponentGroup` so that one
    :meth:`async_update` performs as few round trips as the register layout
    allows -- separately for the input-register telemetry and the
    holding-register settings, since those are two distinct Modbus register
    spaces.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        self._unit = unit

        self.info = DeviceInformation(unit)
        self.pv = PVStrings(unit)
        self.status = InverterStatus(unit)
        self.battery = BatteryTelemetry(unit)
        self.battery_settings = BatterySettings(unit)
        self.grid = GridMeter(unit)
        self.backup = BackupPower(unit)
        self.energy = EnergyTotals(unit)
        self.controls = Controls(unit)

        self._group = ComponentGroup(unit, self.components)

    @property
    def components(self) -> tuple[Component, ...]:
        """Return every actively polled subsystem."""
        return (
            self.info,
            self.pv,
            self.status,
            self.battery,
            self.battery_settings,
            self.grid,
            self.backup,
            self.energy,
            self.controls,
        )

    async def async_update(self) -> None:
        """Refresh every subsystem, pooling reads per register space."""
        await self._group.async_update()

    async def async_start(self) -> None:
        """Send the inverter start command."""
        await async_start_inverter(self._unit)

    async def async_stop(self) -> None:
        """Send the inverter stop command."""
        await async_stop_inverter(self._unit)

    @property
    def is_pv_generating(self) -> bool | None:
        """Whether any PV string is currently producing power."""
        return self.pv.is_generating

    @property
    def is_battery_charging(self) -> bool | None:
        """Whether the battery is currently charging."""
        return self.battery.is_charging

    @property
    def is_battery_discharging(self) -> bool | None:
        """Whether the battery is currently discharging."""
        return self.battery.is_discharging

    @property
    def is_importing_from_grid(self) -> bool | None:
        """Whether the site is currently importing power from the grid."""
        return self.grid.is_importing

    @property
    def is_exporting_to_grid(self) -> bool | None:
        """Whether the site is currently exporting power to the grid."""
        return self.grid.is_exporting

    @property
    def battery_level_nominal(self) -> float | None:
        """Battery level rescaled into the configured min/max SoC band."""
        return self.battery.nominal_level(
            self.battery_settings.min_soc, self.battery_settings.max_soc
        )

    @property
    def battery_usable_charge_kwh(self) -> float | None:
        """Usable stored battery energy (kWh) within the configured SoC band."""
        return self.battery.usable_charge_kwh(
            self.battery_settings.min_soc, self.battery_settings.max_soc
        )

    @property
    def battery_health_rated_charge_kwh(self) -> float | None:
        """Usable stored battery energy (kWh), further scaled by state of health."""
        return self.battery.health_rated_charge_kwh(
            self.battery_settings.min_soc, self.battery_settings.max_soc
        )
