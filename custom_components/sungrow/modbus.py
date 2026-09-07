"""
Build a ``modbus_connection`` connection from a config entry.

Unlike the Home Assistant core integration (which borrows a unit from a
shared ``modbus_connection`` config entry), this HACS package owns its
Modbus link outright: it depends only on the ``modbus-connection`` PyPI
package, so it works on any Home Assistant install without waiting on a
core component.
"""

from __future__ import annotations

from typing import Any

from homeassistant.const import CONF_HOST, CONF_PORT
from modbus_connection import ModbusConnection, ModbusSerialParams, ModbusTcpParams
from modbus_connection.pymodbus import PymodbusConnection

from .const import (
    CONF_MODBUS_TYPE,
    CONF_SERIAL_BAUDRATE,
    CONF_SERIAL_BYTESIZE,
    CONF_SERIAL_PARITY,
    CONF_SERIAL_STOPBITS,
    MODBUS_TYPE_SERIAL,
)


def build_connection(data: dict[str, Any]) -> ModbusConnection:
    """Build a (not-yet-connected) ``ModbusConnection`` from config entry data."""
    if data[CONF_MODBUS_TYPE] == MODBUS_TYPE_SERIAL:
        params = ModbusSerialParams(
            device=data[CONF_HOST],
            baudrate=data[CONF_SERIAL_BAUDRATE],
            parity=data[CONF_SERIAL_PARITY],
            stopbits=data[CONF_SERIAL_STOPBITS],
            bytesize=data[CONF_SERIAL_BYTESIZE],
        )
    else:
        params = ModbusTcpParams(
            host=data[CONF_HOST], port=data[CONF_PORT], framer="socket"
        )
    return PymodbusConnection(params)
