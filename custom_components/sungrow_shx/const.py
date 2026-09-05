"""Constants for the Sungrow SHx custom integration."""

from __future__ import annotations

from datetime import timedelta
from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN: Final = "sungrow_shx"

CONF_MODBUS_TYPE: Final = "modbus_type"
CONF_UNIT_ID: Final = "unit_id"
CONF_SERIAL_PARITY: Final = "parity"
CONF_SERIAL_BAUDRATE: Final = "baudrate"
CONF_SERIAL_STOPBITS: Final = "stopbits"
CONF_SERIAL_BYTESIZE: Final = "bytesize"

MODBUS_TYPE_TCP: Final = "tcp"
MODBUS_TYPE_SERIAL: Final = "serial"

DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 1  # Sungrow's default Modbus station address
DEFAULT_BAUDRATE: Final = 9600
DEFAULT_PARITY: Final = "N"
DEFAULT_STOPBITS: Final = 1
DEFAULT_BYTESIZE: Final = 8

# The inverter itself only reports new numbers every few seconds; this keeps
# well clear of that without hammering the Modbus link.
SCAN_INTERVAL: Final = timedelta(seconds=15)
