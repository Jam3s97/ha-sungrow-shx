"""DataUpdateCoordinator that polls the Sungrow SHx inverter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusError

from .const import DOMAIN, LOGGER, SCAN_INTERVAL
from .sungrow_modbus import SungrowSHx

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SungrowConfigEntry


class SungrowDataUpdateCoordinator(DataUpdateCoordinator[SungrowSHx]):
    """
    Refreshes every sub-system on a schedule.

    ``SungrowSHx.async_update`` fans out to each component and pools reads by
    register space (input vs. holding), so adding/removing entities never
    changes what is polled.
    """

    config_entry: SungrowConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: SungrowConfigEntry, device: SungrowSHx
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=SCAN_INTERVAL,
        )
        self.device = device

    async def _async_update_data(self) -> SungrowSHx:
        """Poll the inverter."""
        try:
            await self.device.async_update()
        except ModbusError as err:
            msg = f"Error communicating with the inverter: {err}"
            raise UpdateFailed(msg) from err
        return self.device
