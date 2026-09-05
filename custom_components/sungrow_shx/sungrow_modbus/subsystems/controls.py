"""General inverter/site controls that are not battery-specific.

See :class:`sungrow_modbus.subsystems.battery.BatterySettings` for
battery-charge/discharge related holding registers.
"""

from __future__ import annotations

from ..data_model import SungrowComponent, onoff_switch, raw_enum, uint16
from ..enums import EmsMode, LoadAdjustmentMode


class Controls(SungrowComponent):
    """Site-level settings and controls (holding registers)."""

    register_space = "holding"

    load_adjustment_mode = raw_enum(
        13001,
        LoadAdjustmentMode,
        category="control",
        description="Load adjustment mode selection.",
        writable=True,
    )
    load_adjustment_mode_enabled = onoff_switch(
        13010, category="control", description="Enables load adjustment mode."
    )

    ems_mode = raw_enum(
        13049,
        EmsMode,
        category="control",
        description="EMS operating mode selection.",
        writable=True,
    )

    export_power_limit = uint16(
        13073,
        unit="W",
        category="control",
        description="Export power limit setpoint; valid range is reported by "
        "GridMeter.export_power_limit_min/max.",
        writable=True,
    )
    export_power_limit_enabled = onoff_switch(
        13086, category="control", description="Enables the export power limit."
    )
    backup_mode_enabled = onoff_switch(
        13074, category="control", description="Enables backup (EPS) mode."
    )

    active_power_limitation_enabled = uint16(
        13088,
        category="control",
        description="Raw active power limitation enable flag (semantics not "
        "fully documented upstream; exposed as-is).",
        writable=True,
    )
    active_power_limitation_ratio = uint16(
        13089,
        scale=0.1,
        unit="%",
        category="control",
        description="Active power limitation ratio.",
        writable=True,
    )
    apl_shutdown_on_zero_export = uint16(
        31212,
        category="control",
        description="Raw flag controlling shutdown behaviour when the active "
        "power limitation ratio is set to zero.",
        writable=True,
    )
