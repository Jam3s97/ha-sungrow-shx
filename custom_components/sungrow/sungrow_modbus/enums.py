"""Sungrow SHx enumerated register values.

Every mapping below is sourced directly from the community-maintained
``modbus_sungrow.yaml`` register map (mkaiser/Sungrow-SHx-Inverter-Modbus-
Home-Assistant), not reverse-engineered or guessed. Codes not listed by that
project are decoded as ``None`` by ``modbus-connection`` rather than raising,
so an inverter reporting an undocumented code degrades gracefully instead of
breaking a read.
"""

from __future__ import annotations

from enum import IntEnum


class RunningStateCode(IntEnum):
    """Sungrow running-state code (protocol address 12999 / register 13000)."""

    RUNNING = 0x0000  # "Running"
    STOP = 0x0001  # "Stop"
    KEY_STOP = 0x0002  # "Key stop"
    EMERGENCY_STOP = 0x0004  # "Emergency Stop"
    STANDBY = 0x0008  # "Standby"
    STARTING = 0x0020  # "Starting"
    INITIAL_STANDBY = 0x0010  # "Initial standby"
    MICROGRID_OPERATION = 0x0014  # "Microgrid Operation"
    RUNNING_2 = 0x0040  # "Running"
    OFF_GRID_CHARGE = 0x0041  # "Off-grid Charge"
    DERATING_RUNNING = 0x0080  # "Derating Running"
    FAULT = 0x0100  # "Fault"
    UPDATE_FAILED = 0x0200  # "Update Failed"
    RUNNING_IN_MAINTAIN_MODE = 0x0400  # "Running in maintain mode"
    RUNNING_IN_COMPULSORY_FORCED_MODE = 0x0800  # "Running in compulsory (forced) mode"
    RUNNING_OFF_GRID = 0x1000  # "Running (off-grid)"
    UNINITIALIZED = 0x1111  # "Uninitialized"
    INITIAL_STANDBY_2 = 0x1200  # "Initial standby"
    KEY_STOP_2 = 0x1300  # "Key stop"
    STANDBY_2 = 0x1400  # "Standby"
    EMERGENCY_STOP_2 = 0x1500  # "Emergency Stop"
    STARTING_2 = 0x1600  # "Starting"
    AFCI_SELF_TEST_SHUTDOWN = 0x1700  # "AFCI self-test shutdown"
    INTELLIGENT_STATION_BUILDING_STATUS = (
        0x1800  # "Intelligent Station Building Status"
    )
    SAFE_MODE = 0x1900  # "Safe Mode"
    OPEN_LOOP = 0x2000  # "Open loop"
    COMMUNICATE_FAULT = 0x2500  # "Communicate fault"
    RESTARTING = 0x2501  # "Restarting"
    RUNNING_IN_EXTERNAL_EMS_MODE = 0x4000  # "Running in External EMS mode"
    EMERGENCY_CHARGING_OPERATION = 0x4001  # "Emergency Charging Operation"
    STOP_2 = 0x8000  # "Stop"
    FAULT_2 = 0x5500  # "Fault"
    DERATING_RUNNING_2 = 0x8100  # "Derating Running"
    DISPATCH_RUNNING = 0x8200  # "Dispatch Running"
    WARN_RUNNING = 0x9100  # "Warn Running"


class DeviceTypeCode(IntEnum):
    """Sungrow device/model type code (protocol address 4999 / register 5000)."""

    SH3K6 = 0x0D06  # "SH3K6"
    SH4K6 = 0x0D07  # "SH4K6"
    SH5K_20 = 0x0D09  # "SH5K-20"
    SH5K_V13 = 0x0D03  # "SH5K-V13"
    SH3K6_30 = 0x0D0A  # "SH3K6-30"
    SH4K6_30 = 0x0D0B  # "SH4K6-30"
    SH5K_30 = 0x0D0C  # "SH5K-30"
    SH3_0RS = 0x0D17  # "SH3.0RS"
    SH3_6RS = 0x0D0D  # "SH3.6RS"
    SH4_0RS = 0x0D18  # "SH4.0RS"
    SH5_0RS = 0x0D0F  # "SH5.0RS"
    SH6_0RS = 0x0D10  # "SH6.0RS"
    SH8_0RS = 0x0D1A  # "SH8.0RS"
    SH10RS = 0x0D1B  # "SH10RS"
    SH5_0RT = 0x0E00  # "SH5.0RT"
    SH6_0RT = 0x0E01  # "SH6.0RT"
    SH8_0RT = 0x0E02  # "SH8.0RT"
    SH10RT = 0x0E03  # "SH10RT"
    SH5_0RT_20 = 0x0E10  # "SH5.0RT-20"
    SH6_0RT_20 = 0x0E11  # "SH6.0RT-20"
    SH8_0RT_20 = 0x0E12  # "SH8.0RT-20"
    SH10RT_20 = 0x0E13  # "SH10RT-20"
    SH5_0RT_V112 = 0x0E0C  # "SH5.0RT-V112"
    SH6_0RT_V112 = 0x0E0D  # "SH6.0RT-V112"
    SH8_0RT_V112 = 0x0E0E  # "SH8.0RT-V112"
    SH10RT_V112 = 0x0E0F  # "SH10RT-V112"
    SH5_0RT_V122 = 0x0E08  # "SH5.0RT-V122"
    SH6_0RT_V122 = 0x0E09  # "SH6.0RT-V122"
    SH8_0RT_V122 = 0x0E0A  # "SH8.0RT-V122"
    SH10RT_V122 = 0x0E0B  # "SH10RT-V122"
    SH5T = 0x0E20  # "SH5T"
    SH6T = 0x0E21  # "SH6T"
    SH8T = 0x0E22  # "SH8T"
    SH10T = 0x0E23  # "SH10T"
    SH12T = 0x0E24  # "SH12T"
    SH15T = 0x0E25  # "SH15T"
    SH20T = 0x0E26  # "SH20T"
    SH25T = 0x0E28  # "SH25T"
    MG5RL = 0x0D27  # "MG5RL"
    MG6RL = 0x0D28  # "MG6RL"


class EmsMode(IntEnum):
    """EMS operating mode selector (protocol address 13049 / register 13050)."""

    SELF_CONSUMPTION = 0  # default
    FORCED_MODE = 2  # datasheet also calls this "compulsory mode"
    EXTERNAL_EMS = 3
    VPP = 4
    # MICROGRID = 8  # rarely used; left out of the default option set


class ForcedChargeDischargeCommand(IntEnum):
    """Forced charge/discharge command (protocol address 13050 / register 13051)."""

    STOP = 0xCC  # default
    FORCED_CHARGE = 0xAA
    FORCED_DISCHARGE = 0xBB


class LoadAdjustmentMode(IntEnum):
    """Load adjustment mode selector (protocol address 13001 / register 13002)."""

    TIMING = 0
    ON_OFF = 1
    POWER_OPTIMIZATION = 2
    DISABLED = 3  # default


class OnOffCode(IntEnum):
    """The 0xAA/0x55 "virtual switch" convention used by several holding registers.

    Sungrow's write-enable style registers (backup mode, export power limit
    enable, load adjustment mode enable, ...) use these two magic bytes
    instead of a plain 0/1 flag.
    """

    ON = 0xAA
    OFF = 0x55


class InverterControlCommand(IntEnum):
    """Start/stop command written to the running-state register.

    This is a write-only control code: it is written to the same protocol
    address (12999) that :class:`RunningStateCode` is read from, but the two
    are not the same value space, so it is deliberately not modelled as a
    regular writable field -- see
    :func:`sungrow_modbus.data_model.async_start_inverter` and
    :func:`sungrow_modbus.data_model.async_stop_inverter`.
    """

    START = 0xCF
    STOP = 0xCE
