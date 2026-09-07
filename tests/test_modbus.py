"""Tests for ``modbus.py::build_params``."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from modbus_connection import ModbusSerialParams, ModbusTcpParams

from custom_components.sungrow.const import (
    CONF_MODBUS_TYPE,
    CONF_SERIAL_BAUDRATE,
    CONF_SERIAL_BYTESIZE,
    CONF_SERIAL_PARITY,
    CONF_SERIAL_STOPBITS,
    MODBUS_TYPE_SERIAL,
    MODBUS_TYPE_TCP,
)
from custom_components.sungrow.modbus import build_params


def test_build_params_tcp() -> None:
    params = build_params(
        {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP, CONF_HOST: "10.0.0.5", CONF_PORT: 502}
    )
    assert params == ModbusTcpParams(host="10.0.0.5", port=502, framer="socket")


def test_build_params_serial() -> None:
    params = build_params(
        {
            CONF_MODBUS_TYPE: MODBUS_TYPE_SERIAL,
            CONF_HOST: "/dev/ttyUSB0",
            CONF_SERIAL_BAUDRATE: 9600,
            CONF_SERIAL_PARITY: "N",
            CONF_SERIAL_STOPBITS: 1,
            CONF_SERIAL_BYTESIZE: 8,
        }
    )
    assert params == ModbusSerialParams(
        device="/dev/ttyUSB0", baudrate=9600, parity="N", stopbits=1, bytesize=8
    )
