# Sungrow for Home Assistant

[![hacs][hacs-badge]][hacs-url]
[![Validate][validate-badge]][validate-url]
[![Lint][lint-badge]][lint-url]

> [!WARNING]
> **This is experimental development code and is NOT ready for production use.** Expect breaking changes, bugs, and incomplete features. Use at your own risk, and avoid deploying it against inverters or setups you depend on.

A [HACS](https://hacs.xyz/) custom integration for **Sungrow SHx** hybrid inverters (SH3.0RS through SH25T, with an SBR-series or compatible battery), talking directly to the inverter over Modbus TCP or a serial/RS485 gateway. No cloud account, no iSolarCloud dependency.

This repository packages [`sungrow-modbus`](https://pypi.org/project/sungrow-modbus/) -- a standalone, transport-independent Modbus device library -- into a ready-to-install Home Assistant custom component. The library is vendored under `custom_components/sungrow/sungrow_modbus/` so the integration has no dependency on a matching PyPI release landing first; only the underlying `modbus-connection` framework is installed from PyPI.

The integration gets its Modbus connection from Home Assistant core's own Modbus integration (requires HA 2026.9 or newer), which pools one connection per physical endpoint across every integration or config entry talking to the same device -- useful since some inverters and RS485 gateways only accept a handful of simultaneous Modbus sessions.

## What you get

* One device per inverter, with entities for:
  * **Sensors**: PV string voltage/current/power, inverter AC output (voltage/current/power/temperature/power factor), battery telemetry (power, voltage, level, health, temperature), grid meter (power, voltage, current, frequency, import/export split), backup output, running-state, and daily/lifetime energy counters -- generated automatically from every read-only register the library declares, so nothing needs to be added by hand as the library grows.
  * **Binary sensors**: PV generating, battery charging, importing from grid, running.
  * **Numbers**: min/max battery SoC, reserved backup SoC, forced charge/discharge power, export power limit, max charge/discharge power, charge/discharge start-power thresholds.
  * **Selects**: EMS mode, load adjustment mode, forced charge/discharge command.
  * **Switches**: backup mode, export power limit enable, load adjustment mode enable.
  * **Buttons**: start inverter, stop inverter.

## Installation

### HACS (recommended)

1. In HACS, go to *Integrations* → the three-dot menu → *Custom repositories*, and add this repository's URL with category *Integration* (only needed until this integration is available in the default HACS catalog).
2. Search for "Sungrow" in HACS and install it.
3. Restart Home Assistant.
4. Go to *Settings → Devices & Services → Add Integration*, search for "Sungrow", and follow the prompts.

### Manual

Copy `custom_components/sungrow` into your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration as above.

## Configuration

All configuration happens through the UI -- there is no YAML setup.

* **TCP**: host/IP of the inverter or its LAN/Wi-Fi dongle, port (default 502), and the Modbus unit/station address (default 1).
* **Serial**: the serial device path (e.g. `/dev/ttyUSB0`), baud rate, parity, stop bits, data bits, and the Modbus unit address, for an RS485 gateway.

## Known limitations

* Tested against the SH-RT/SH-RS/SHT register map used by the community `modbus_sungrow.yaml` project; older single-phase SGxxxRT/HX models are not covered.
* Writable registers are exposed as-is; the integration does not attempt to validate combinations (e.g. setting a forced-charge command while EMS mode is not compatible with it) beyond the per-field min/max the inverter itself documents.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). This repository follows the [`integration_blueprint`](https://github.com/ludeeus/integration_blueprint) project layout, so anything documented there about `scripts/setup`, `scripts/develop`, `scripts/lint`, and the devcontainer applies here unchanged.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
[validate-badge]: https://github.com/Jam3s97/ha-sungrow-shx/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/Jam3s97/ha-sungrow-shx/actions/workflows/validate.yml
[lint-badge]: https://github.com/Jam3s97/ha-sungrow-shx/actions/workflows/lint.yml/badge.svg
[lint-url]: https://github.com/Jam3s97/ha-sungrow-shx/actions/workflows/lint.yml
