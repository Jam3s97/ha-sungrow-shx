# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A [HACS](https://hacs.xyz/) custom integration for **Sungrow SHx** hybrid inverters (SH3.0RS through SH25T), talking directly to the inverter over Modbus TCP or serial/RS485 -- no cloud/iSolarCloud dependency. It follows the [`integration_blueprint`](https://github.com/ludeeus/integration_blueprint) project layout.

The integration is standalone by design: it owns its own Modbus connection via the `modbus-connection` PyPI package rather than depending on Home Assistant core's shared Modbus component, so it installs and works without waiting on anything upstream.

## Commands

```bash
scripts/setup     # install requirements_common.txt + requirements_dev.txt
scripts/develop   # run a local HA instance against ./config with the integration loaded (PYTHONPATH trick, no symlinks)
scripts/lint      # ruff format . && ruff check . --fix
```

There is no test suite in this repo. CI (`.github/workflows/`) runs `ruff check` / `ruff format --check` (lint.yml) and `hassfest` + `hacs` structural validation (validate.yml) on every push/PR to `main`.

Ruff config (`.ruff.toml`) selects `ALL` rules, targets py314, and excludes `custom_components/sungrow/sungrow_modbus/` from formatting -- that directory is a vendored library with its own upstream style (see below).

## Architecture

### Two layers: HA integration vs. vendored device library

`custom_components/sungrow/` has two distinct layers that must not be conflated:

1. **`sungrow_modbus/`** -- a vendored, transport-independent device library (mirrors the PyPI package [`sungrow-modbus`](https://pypi.org/project/sungrow-modbus/)). It knows nothing about Home Assistant. It models the inverter as a `SungrowSHx` object composed of `Component` subsystems (from the `modbus_connection.model` framework), each owning a Modbus register block. It is vendored so the integration isn't blocked on a matching PyPI release; the underlying `modbus-connection` transport library is a real PyPI dependency (see `manifest.json`).
2. **Everything else in `custom_components/sungrow/`** -- the HA integration proper: config flow, coordinator, and one file per HA platform (`sensor.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`, `button.py`).

### Metadata-driven entity generation (the key mechanism)

Entities are **not** hand-listed per platform. Every register field declared in `sungrow_modbus/data_model.py` (via helpers like `uint16`, `int16`, `raw_enum`, `onoff_switch`, ...) carries an attached `DatapointMetadata` (`sungrow_modbus/metadata.py`) describing its `value_kind` (`number`/`enum`/`boolean`/`string`), writability, unit, min/max/step, etc.

- `field_index.py` (`iter_fields`) walks every subsystem component on `SungrowSHx` and yields a `FieldRef` for each metadata-tagged field, deriving a stable entity key (`{component}_{attribute}`) and a human name.
- Each platform module (`sensor.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`) filters `iter_fields()` by `value_kind` / `writable` and builds its entity descriptions from that -- e.g. `sensor.py` takes all non-writable fields, `number.py` takes writable `number` fields.
- `unit_mapping.py` maps `DatapointMetadata` to HA units/device classes/state classes/entity categories.

**Consequence:** adding or changing a register in `sungrow_modbus/data_model.py` (or a subsystem in `sungrow_modbus/subsystems/`) automatically surfaces it as the right kind of HA entity across the relevant platform(s) -- no platform-side changes needed, unless the field needs to be excluded/overridden (see `field_index.py`'s `_READ_ONLY_OVERRIDE`).

### Runtime flow

- `__init__.py::async_setup_entry` builds a `ModbusConnection` (`modbus.py::build_connection`, TCP or serial from config entry data), connects, wraps a `ModbusUnit` in a `SungrowSHx` device object, and creates a `SungrowDataUpdateCoordinator`.
- `coordinator.py` is a standard `DataUpdateCoordinator[SungrowSHx]` polling every `SCAN_INTERVAL` (15s, `const.py`). Its `_async_update_data` calls `device.async_update()`.
- `SungrowSHx.async_update()` (`sungrow_modbus/sungrow.py`) delegates to a single `ComponentGroup.async_update()`, which pools reads per Modbus register space (input vs. holding) across all subsystems -- so the number of entities never changes the number of round trips.
- Every entity subclasses `SungrowEntity` (`entity.py`), which resolves its subsystem via `getattr(coordinator.device, component)` and shares one `DeviceInfo` (one HA device per inverter).
- Writes go through the owning subsystem's `.write(attribute, value)` (see `number.py`, `select.py`, `switch.py`), then request a coordinator refresh.

### Subsystems (`sungrow_modbus/subsystems/`)

Each file (`pv.py`, `inverter.py`, `battery.py`, `grid.py`, `backup.py`, `energy.py`, `controls.py`) is a `SungrowComponent` bound to either the input-register (telemetry) or holding-register (settings/control) space -- never both, per `SungrowComponent`'s docstring in `data_model.py`. `sungrow.py` composes all of them plus `DeviceInformation` (`device_info.py`) into `SungrowSHx`.

## Conventions

- Config is UI-only (config flow), no YAML setup.
- The HA-facing identity (domain `sungrow`, manifest/HACS display name "Sungrow") is deliberately broader than the vendored library's `SungrowSHx`/`sungrow_modbus` naming, which stays scoped to the SHx (SH-RS/SH-RT/SHT) register map it actually implements today -- don't rename the library to match if the domain or display name changes again.
- `sungrow_modbus/` keeps its own vendored formatting/lint posture (excluded from the house ruff config) since it mirrors an upstream package -- don't reformat it to match the rest of the repo.
- When a register is technically writable but unsafe/meaningless to expose as a raw control in HA, mark it in `field_index.py`'s `_READ_ONLY_OVERRIDE` rather than special-casing it in a platform module.
