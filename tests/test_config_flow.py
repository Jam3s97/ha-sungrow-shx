"""Tests for the Sungrow config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from modbus_connection import ModbusError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sungrow.const import (
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

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit


async def test_user_step_shows_type_choice(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_tcp_flow_creates_entry(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    # The flow's own read uses async_get_temporary_unit; the config entry
    # created below is set up immediately afterwards (a background task) and
    # goes through async_get_unit like any other entry -- both need the mock.
    patch_async_get_temporary_unit(loaded_unit)
    patch_async_get_unit(loaded_unit)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    assert result["step_id"] == "tcp"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )
    assert result["step_id"] == "migrating"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"migrating_from_legacy": False}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "SH10RT"
    assert result["data"][CONF_HOST] == "10.0.0.5"
    assert result["data"][CONF_MODBUS_TYPE] == MODBUS_TYPE_TCP
    assert result["data"][CONF_LEGACY_NAMING] is False


async def test_not_migrating_skips_legacy_naming_step(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    """Answering "no" to the migration question never shows the naming step."""
    patch_async_get_temporary_unit(loaded_unit)
    patch_async_get_unit(loaded_unit)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"migrating_from_legacy": False}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LEGACY_NAMING] is False


async def test_legacy_naming_step_warns_of_active_legacy_entities(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
) -> None:
    patch_async_get_temporary_unit(loaded_unit)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", "modbus", "sg_total_dc_power", suggested_object_id="total_dc_power"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"migrating_from_legacy": True}
    )

    assert result["step_id"] == "legacy_naming"
    assert result["description_placeholders"]["legacy_warning"] != ""


async def test_legacy_naming_blocks_claim_while_legacy_entities_active(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    """Trying to claim legacy ids while the old entities are still live is refused."""
    patch_async_get_temporary_unit(loaded_unit)
    patch_async_get_unit(loaded_unit)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", "modbus", "sg_total_dc_power", suggested_object_id="total_dc_power"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"migrating_from_legacy": True}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LEGACY_NAMING: True}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "legacy_naming"
    assert result["errors"] == {"base": "legacy_entities_active"}

    # Choosing modern ids instead is never blocked -- nothing to claim.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LEGACY_NAMING: False}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_LEGACY_NAMING] is False


async def test_serial_flow_creates_entry(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
    patch_async_get_unit: Callable[[MockModbusUnit], None],
) -> None:
    patch_async_get_temporary_unit(loaded_unit)
    patch_async_get_unit(loaded_unit)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_SERIAL}
    )
    assert result["step_id"] == "serial"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "/dev/ttyUSB0",
            CONF_SERIAL_BAUDRATE: DEFAULT_BAUDRATE,
            CONF_SERIAL_PARITY: DEFAULT_PARITY,
            CONF_SERIAL_STOPBITS: str(DEFAULT_STOPBITS),
            CONF_SERIAL_BYTESIZE: str(DEFAULT_BYTESIZE),
            CONF_UNIT_ID: DEFAULT_UNIT_ID,
        },
    )
    assert result["step_id"] == "migrating"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"migrating_from_legacy": True}
    )
    assert result["step_id"] == "legacy_naming"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LEGACY_NAMING: True}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MODBUS_TYPE] == MODBUS_TYPE_SERIAL
    assert result["data"][CONF_LEGACY_NAMING] is True


async def test_cannot_connect_re_shows_form_with_error(
    hass: HomeAssistant,
    patch_async_get_temporary_unit: Callable[[Exception], None],
) -> None:
    patch_async_get_temporary_unit(ModbusError("unreachable"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tcp"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_unit_aborts(
    hass: HomeAssistant,
    loaded_unit: MockModbusUnit,
    patch_async_get_temporary_unit: Callable[[MockModbusUnit], None],
) -> None:
    patch_async_get_temporary_unit(loaded_unit)
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="tcp_10.0.0.5_1",
        data={
            CONF_MODBUS_TYPE: MODBUS_TYPE_TCP,
            CONF_HOST: "10.0.0.5",
            CONF_PORT: DEFAULT_PORT,
            CONF_UNIT_ID: DEFAULT_UNIT_ID,
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_MODBUS_TYPE: MODBUS_TYPE_TCP}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.5", CONF_PORT: DEFAULT_PORT, CONF_UNIT_ID: DEFAULT_UNIT_ID},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
