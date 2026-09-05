"""Read a Sungrow SHx hybrid inverter over Modbus.

A standalone device-modelling library built on ``modbus-connection``. It has
no dependency on, or knowledge of, Home Assistant -- see
https://developers.home-assistant.io/docs/modbus/introduction for the
Home Assistant integration pattern this library is designed to plug into.
"""

from __future__ import annotations

from .device_info import DeviceInformation
from .enums import (
    DeviceTypeCode,
    EmsMode,
    ForcedChargeDischargeCommand,
    InverterControlCommand,
    LoadAdjustmentMode,
    OnOffCode,
    RunningStateCode,
)
from .exceptions import SungrowError, SungrowValueValidationError
from .sungrow import SungrowSHx

__all__ = [
    "DeviceInformation",
    "DeviceTypeCode",
    "EmsMode",
    "ForcedChargeDischargeCommand",
    "InverterControlCommand",
    "LoadAdjustmentMode",
    "OnOffCode",
    "RunningStateCode",
    "SungrowError",
    "SungrowSHx",
    "SungrowValueValidationError",
]

__version__ = "0.1.0"
