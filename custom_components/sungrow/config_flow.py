"""Config flow for the Sungrow custom integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
)
from modbus_connection import ModbusError

from . import legacy_naming
from .const import (
    CONF_LEGACY_NAMING,
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
from .modbus import build_params
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

# Flow-internal only -- not stored in the config entry. Just routes whether
# async_step_legacy_naming is shown at all; a "no" here is equivalent to
# CONF_LEGACY_NAMING=False without asking a second question.
_KEY_MIGRATING = "migrating_from_legacy"
STEP_MIGRATING = vol.Schema({vol.Required(_KEY_MIGRATING, default=False): bool})

# Default True here (unlike the migrating question above): by the time this
# step shows, the user has already said they're migrating, so keeping the
# legacy ids is the sensible default -- see translations/en.json.
STEP_LEGACY_NAMING = vol.Schema({vol.Required(CONF_LEGACY_NAMING, default=True): bool})


class SungrowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Sungrow custom integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._modbus_type: str = MODBUS_TYPE_TCP
        self._pending_data: dict[str, Any] = {}
        self._pending_title: str = ""

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
                self._pending_data = data
                self._pending_title = title
                return await self.async_step_migrating()
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def async_step_migrating(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask whether this is a migration from the legacy YAML package."""
        if user_input is not None:
            if not user_input[_KEY_MIGRATING]:
                data = {**self._pending_data, CONF_LEGACY_NAMING: False}
                return self.async_create_entry(title=self._pending_title, data=data)
            return await self.async_step_legacy_naming()
        return self.async_show_form(step_id="migrating", data_schema=STEP_MIGRATING)

    async def async_step_legacy_naming(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask whether to keep the legacy YAML package's entity ids."""
        registry = er.async_get(self.hass)
        active = [
            entity_id
            for entity_id in legacy_naming.all_legacy_entity_ids()
            if registry.async_is_registered(entity_id)
        ]

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_LEGACY_NAMING] and active:
                # Claiming would silently land on sensor.foo_2 instead of
                # sensor.foo -- refuse rather than let that happen quietly.
                errors["base"] = "legacy_entities_active"
            else:
                data = {**self._pending_data, **user_input}
                return self.async_create_entry(title=self._pending_title, data=data)

        warning = ""
        if active:
            warning = (
                f"\n\n{len(active)} legacy entities are still registered "
                "(e.g. from the YAML package). Remove it and restart Home "
                "Assistant first, or your old entity ids may not be free to "
                "claim."
            )
        return self.async_show_form(
            step_id="legacy_naming",
            data_schema=STEP_LEGACY_NAMING,
            description_placeholders={"legacy_warning": warning},
            errors=errors,
        )

    async def _async_title(self, data: dict[str, Any]) -> str | None:
        """Read the inverter model over a temporary Modbus unit, for the entry title."""
        params = build_params(data)
        try:
            async with async_get_temporary_unit(
                self.hass, params, int(data[CONF_UNIT_ID])
            ) as unit:
                device = SungrowSHx(unit)
                await device.info.async_update()
        except ModbusError, OSError, ValueError, HomeAssistantError:
            return None
        return device.info.model
