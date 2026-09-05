"""Config flow for the Sungrow SHx custom integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
)
from modbus_connection import ModbusError

from .const import (
    CONF_MODBUS_TYPE,
    CONF_SERIAL_BAUDRATE,
    CONF_SERIAL_BYTESIZE,
    CONF_SERIAL_PARITY,
    CONF_SERIAL_STOPBITS,
    CONF_UNIT_ID,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_PORT,
    DEFAULT_STOPBITS,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MODBUS_TYPE_SERIAL,
    MODBUS_TYPE_TCP,
)
from .modbus import build_connection
from .sungrow_modbus import SungrowSHx

STEP_TYPE = vol.Schema(
    {
        vol.Required(CONF_MODBUS_TYPE, default=MODBUS_TYPE_TCP): SelectSelector(
            SelectSelectorConfig(options=[MODBUS_TYPE_TCP, MODBUS_TYPE_SERIAL])
        ),
    }
)

STEP_TCP = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): NumberSelector(
            NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)
        ),
    }
)

STEP_SERIAL = vol.Schema(
    {
        vol.Required(CONF_HOST): str,  # serial device path, e.g. /dev/ttyUSB0
        vol.Required(CONF_SERIAL_BAUDRATE, default=DEFAULT_BAUDRATE): int,
        vol.Required(CONF_SERIAL_PARITY, default=DEFAULT_PARITY): SelectSelector(
            SelectSelectorConfig(options=["N", "E", "O"])
        ),
        vol.Required(CONF_SERIAL_STOPBITS, default=DEFAULT_STOPBITS): SelectSelector(
            SelectSelectorConfig(options=["1", "2"])
        ),
        vol.Required(CONF_SERIAL_BYTESIZE, default=DEFAULT_BYTESIZE): SelectSelector(
            SelectSelectorConfig(options=["7", "8"])
        ),
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): NumberSelector(
            NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)
        ),
    }
)


class SungrowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Sungrow SHx custom integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._modbus_type: str = MODBUS_TYPE_TCP

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose TCP or serial before asking for the matching details."""
        if user_input is not None:
            self._modbus_type = user_input[CONF_MODBUS_TYPE]
            if self._modbus_type == MODBUS_TYPE_SERIAL:
                return await self.async_step_serial()
            return await self.async_step_tcp()
        return self.async_show_form(step_id="user", data_schema=STEP_TYPE)

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for TCP connection details."""
        return await self._async_step_connection("tcp", STEP_TCP, user_input)

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for serial connection details."""
        return await self._async_step_connection("serial", STEP_SERIAL, user_input)

    async def _async_step_connection(
        self,
        step_id: str,
        schema: vol.Schema,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {CONF_MODBUS_TYPE: self._modbus_type, **user_input}
            await self.async_set_unique_id(
                f"{self._modbus_type}_{data[CONF_HOST]}_{int(data[CONF_UNIT_ID])}"
            )
            self._abort_if_unique_id_configured()
            if (title := await self._async_title(data)) is None:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=title, data=data)
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def _async_title(self, data: dict[str, Any]) -> str | None:
        """Connect, read the inverter model for the entry title, then disconnect."""
        connection = build_connection(data)
        try:
            await connection.connect()
        except (ModbusError, OSError, ValueError):
            return None
        try:
            device = SungrowSHx(connection.for_unit(int(data[CONF_UNIT_ID])))
            await device.info.async_update()
        except (ModbusError, OSError, ValueError):
            return None
        finally:
            await connection.close()
        return device.info.model
