"""
Build the Modbus connection parameters for a config entry.

The connection itself comes from Home Assistant core's Modbus integration
(``homeassistant.components.modbus``), which shares one connection per
physical endpoint across every integration that asks it for a unit -- see
:mod:`.__init__` and :mod:`.config_flow`. This module only describes which
endpoint and link settings to ask for.
"""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_HOST, CONF_PORT
from modbus_connection import ModbusSerialParams, ModbusTcpParams

from .const import (
    CONF_MODBUS_TYPE,
    CONF_SERIAL_BAUDRATE,
    CONF_SERIAL_BYTESIZE,
    CONF_SERIAL_PARITY,
    CONF_SERIAL_STOPBITS,
    MODBUS_TYPE_SERIAL,
)


def build_params(data: dict[str, Any]) -> ModbusTcpParams | ModbusSerialParams:
    """Build the connection parameters describing the endpoint to reach."""
    if data[CONF_MODBUS_TYPE] == MODBUS_TYPE_SERIAL:
        return ModbusSerialParams(
            device=data[CONF_HOST],
            baudrate=data[CONF_SERIAL_BAUDRATE],
            parity=data[CONF_SERIAL_PARITY],
            stopbits=data[CONF_SERIAL_STOPBITS],
            bytesize=data[CONF_SERIAL_BYTESIZE],
        )
    return ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT], framer="socket")
