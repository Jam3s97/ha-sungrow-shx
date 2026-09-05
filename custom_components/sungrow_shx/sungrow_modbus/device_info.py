"""Device identity: model, serial number and firmware/protocol versions."""

from __future__ import annotations

from .data_model import SungrowComponent, ascii_string, uint16
from .enums import DeviceTypeCode


class DeviceInformation(SungrowComponent):
    """Controller identity, split across several input-register strings.

    Sungrow reports firmware as four concatenated version strings (the
    fourth only present on battery-equipped systems) plus separate ARM/DSP
    software strings and a numeric protocol version. All of it lives in the
    input register space.
    """

    register_space = "input"

    _version_part_1 = ascii_string(
        2581, 11, description="First segment of the combined firmware string."
    )
    _version_part_2 = ascii_string(
        2596, 11, description="Second segment of the combined firmware string."
    )
    _version_part_3 = ascii_string(
        2612, 11, description="Third segment of the combined firmware string."
    )
    _version_part_4 = ascii_string(
        2628,
        11,
        description="Fourth segment of the combined firmware string "
        "(battery systems only).",
    )
    protocol_version_raw = uint16(
        4951, category="identity", description="Communication protocol version."
    )
    arm_software = ascii_string(4953, 15, description="ARM controller software.")
    dsp_software = ascii_string(4968, 15, description="DSP controller software.")
    serial_number = ascii_string(4989, 10, description="Inverter serial number.")
    device_type_code_raw = uint16(
        4999, category="identity", description="Raw device/model type code."
    )
    rated_output_power = uint16(
        5000,
        scale=100,
        unit="W",
        category="identity",
        description="Inverter rated output power.",
    )
    inverter_firmware_version = ascii_string(
        13249, 15, description="Inverter firmware version string."
    )
    communication_module_firmware_version = ascii_string(
        13264, 15, description="Communication (Wi-Fi/LAN dongle) firmware version."
    )
    battery_firmware_version = ascii_string(
        13279, 15, description="Battery BMS firmware version (if fitted)."
    )

    @property
    def manufacturer(self) -> str:
        """Controller manufacturer."""
        return "Sungrow"

    @property
    def firmware_version(self) -> str | None:
        """The combined firmware string, e.g. 'SAPPHIRE-H_01011.95.12...'.

        Concatenates the up-to-four raw version segments, dropping any that
        were not read (battery segment absent on systems without a battery).
        """
        parts = (
            self._version_part_1,
            self._version_part_2,
            self._version_part_3,
            self._version_part_4,
        )
        available = [part for part in parts if part]
        return "".join(available) if available else None

    @property
    def device_type(self) -> DeviceTypeCode | None:
        """The decoded device/model type, or ``None`` if the code is unknown."""
        raw = self.device_type_code_raw
        if raw is None:
            return None
        try:
            return DeviceTypeCode(raw)
        except ValueError:
            return None

    @property
    def model(self) -> str:
        """Model name, e.g. 'SH10RT', falling back to the raw code or a generic name."""
        device_type = self.device_type
        if device_type is not None:
            return device_type.name.replace("_", ".")
        if self.device_type_code_raw is not None:
            return f"Sungrow SHx (type 0x{self.device_type_code_raw:04X})"
        return "Sungrow SHx"

    @property
    def protocol_version(self) -> str | None:
        """Protocol version formatted like 'V<major>.<minor>' where known."""
        raw = self.protocol_version_raw
        return str(raw) if raw is not None else None
