# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A [HACS](https://hacs.xyz/) custom integration for **Sungrow SHx** hybrid inverters (SH3.0RS through SH25T), talking directly to the inverter over Modbus TCP or serial/RS485 -- no cloud/iSolarCloud dependency. It follows the [`integration_blueprint`](https://github.com/ludeeus/integration_blueprint) project layout.

The integration gets its Modbus connection from Home Assistant core's Modbus integration (`homeassistant.components.modbus.async_get_unit`/`async_get_temporary_unit`, shipped in HA 2026.9 -- see "Modernizing Modbus in Home Assistant 2026.9"), which pools one connection per physical endpoint across every integration/entry that asks for a unit on it. This is a hard `dependencies: ["modbus"]` in `manifest.json`, and sets the HACS-declared minimum HA version (`hacs.json`) to `2026.9.0`.

## Commands

```bash
scripts/setup       # install requirements_common.txt + requirements_test.txt (dev + lint + test, transitively)
scripts/develop     # run a local HA instance against ./config with the integration loaded (PYTHONPATH trick, no symlinks)
scripts/lint        # ruff format . && ruff check . --fix
scripts/test        # pytest (accepts pytest args, e.g. scripts/test -k config_flow)
scripts/sync-vendor # pull custom_components/sungrow/sungrow_modbus/ from github.com/Jam3s97/sungrow-modbus (default ref: develop)
scripts/generate_legacy_entity_map.py [--check] # regenerate custom_components/sungrow/legacy_entity_map.json (needs dev/legacy_reference/modbus_sungrow.yaml locally, see dev/legacy_reference/README.md)
```

CI (`.github/workflows/`) runs `ruff check` / `ruff format --check` (lint.yml), the `tests/` suite (test.yml), and `hassfest` + `hacs` structural validation (validate.yml) on every push/PR to `main`.

### Tests (`tests/`)

Everything under `tests/` runs against `modbus_connection`'s in-memory mock backend (`MockModbusUnit`, via its auto-registered pytest plugin) and `pytest-homeassistant-custom-component` -- never real hardware or a real socket. `homeassistant.components.modbus.async_get_unit`/`async_get_temporary_unit` are monkeypatched (see `patch_async_get_unit`/`patch_async_get_temporary_unit` in `tests/conftest.py`) to hand out the mock unit instead of opening a connection, so the full config-flow -> setup -> entity-generation path is exercised without touching Modbus at all. `tests/conftest.py::loaded_unit` preloads one realistic register per field the suite exercises; `setup_integration` fully sets up a config entry against it for the platform tests, which look entities up by `unique_id` through the entity registry (`tests/helpers.py::entity_id_for`) rather than by guessing entity_ids. Note `requirements_test.txt` also pins `pymodbus` directly: `manifest.json`'s hard `dependencies: ["modbus"]` pulls in HA core's `modbus` component, whose own manifest requires `pymodbus` even though this integration only ever goes through the tmodbus-backed shared connection pool -- HA installs it automatically at runtime, but the test environment needs it pinned explicitly.

Ruff config (`.ruff.toml`) selects `ALL` rules, targets py314, and excludes `custom_components/sungrow/sungrow_modbus/` from formatting -- that directory is a vendored library with its own upstream style (see below).

## Architecture

### Two layers: HA integration vs. vendored device library

`custom_components/sungrow/` has two distinct layers that must not be conflated:

1. **`sungrow_modbus/`** -- a vendored, transport-independent device library, synced from [`github.com/Jam3s97/sungrow-modbus`](https://github.com/Jam3s97/sungrow-modbus) via `scripts/sync-vendor` (and eventually meant to mirror the PyPI package [`sungrow-modbus`](https://pypi.org/project/sungrow-modbus/), not yet published). It knows nothing about Home Assistant or how its `ModbusUnit` was obtained. It models the inverter as a `SungrowSHx` object composed of `Component` subsystems (from the `modbus_connection.model` framework), each owning a Modbus register block. It is vendored so the integration isn't blocked on a matching PyPI release; the underlying `modbus-connection` framework is a real PyPI dependency (see `manifest.json`). Syncing is a manual, on-demand step (run `scripts/sync-vendor [ref]`, default `develop` since upstream lands fixes there before merging to `main`, then review the diff) -- there's no CI job auto-pulling upstream changes.
2. **Everything else in `custom_components/sungrow/`** -- the HA integration proper: config flow, coordinator, `modbus.py` (builds connection *params* only -- see Runtime flow), and one file per HA platform (`sensor.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`, `button.py`).

### Metadata-driven entity generation (the key mechanism)

Entities are **not** hand-listed per platform. Every register field declared in `sungrow_modbus/data_model.py` (via helpers like `uint16`, `int16`, `raw_enum`, `onoff_switch`, ...) carries an attached `DatapointMetadata` (`sungrow_modbus/metadata.py`) describing its `value_kind` (`number`/`enum`/`boolean`/`string`), writability, unit, min/max/step, etc.

- `field_index.py` (`iter_fields`) walks every subsystem component on `SungrowSHx` and yields a `FieldRef` for each metadata-tagged field, deriving a stable entity key (`{component}_{attribute}`) and a human name.
- Each platform module (`sensor.py`, `number.py`, `select.py`, `switch.py`, `binary_sensor.py`) filters `iter_fields()` by `value_kind` / `writable` and builds its entity descriptions from that -- e.g. `sensor.py` takes all non-writable fields, `number.py` takes writable `number` fields.
- `unit_mapping.py` maps `DatapointMetadata` to HA units/device classes/state classes/entity categories.

**Consequence:** adding or changing a register in `sungrow_modbus/data_model.py` (or a subsystem in `sungrow_modbus/subsystems/`) automatically surfaces it as the right kind of HA entity across the relevant platform(s) -- no platform-side changes needed, unless the field needs to be excluded/overridden (see `field_index.py`'s `_READ_ONLY_OVERRIDE`).

### Runtime flow

- `modbus.py::build_params` turns config entry data into a `ModbusTcpParams`/`ModbusSerialParams` describing the endpoint only -- no connection is opened here.
- `__init__.py::async_setup_entry` calls `homeassistant.components.modbus.async_get_unit(hass, entry, params, unit_id)` to get a `ModbusUnit` on HA core's shared connection for that endpoint (pooled with any other integration/entry on the same inverter or gateway), wraps it in a `SungrowSHx` device object, and creates a `SungrowDataUpdateCoordinator`. `entry.runtime_data` *is* the coordinator (no wrapper dataclass) -- every platform's `async_setup_entry` reads it directly. `async_get_unit` performs no I/O and doesn't raise on an unreachable device; that surfaces later, from `coordinator.async_config_entry_first_refresh()` converting the first failed poll into `ConfigEntryNotReady` on its own. HA core owns the connection's lifecycle (closed via `entry.async_on_unload`, registered inside `async_get_unit` itself), so `async_unload_entry` has nothing of its own to close.
- `config_flow.py::_async_title` uses `async_get_temporary_unit` (an async context manager, for use before a config entry exists) to read the device model for the entry title without holding a connection open past the config flow.
- `coordinator.py` is a standard `DataUpdateCoordinator[SungrowSHx]` polling every `SCAN_INTERVAL` (15s, `const.py`). Its `_async_update_data` calls `device.async_update()`.
- `SungrowSHx.async_update()` (`sungrow_modbus/sungrow.py`) delegates to a single `ComponentGroup.async_update()`, which pools reads per Modbus register space (input vs. holding) across all subsystems -- so the number of entities never changes the number of round trips.
- Every entity subclasses `SungrowEntity` (`entity.py`), which resolves its subsystem via `getattr(coordinator.device, component)` and shares one `DeviceInfo` (one HA device per inverter).
- Writes go through the owning subsystem's `.write(attribute, value)` (see `number.py`, `select.py`, `switch.py`), then request a coordinator refresh.

### Subsystems (`sungrow_modbus/subsystems/`)

Each file (`pv.py`, `inverter.py`, `battery.py`, `grid.py`, `backup.py`, `energy.py`, `controls.py`) is a `SungrowComponent` bound to either the input-register (telemetry) or holding-register (settings/control) space -- never both, per `SungrowComponent`'s docstring in `data_model.py`. `sungrow.py` composes all of them plus `DeviceInformation` (`device_info.py`) into `SungrowSHx`.

## Migrating from the legacy YAML package

A long-running YAML Modbus package
([`mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant`](https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant))
covers the same inverters and has years of users whose recorder history,
long-term statistics, dashboards, and automations are keyed by its
`entity_id`s. `custom_components/sungrow/legacy_entity_map.json` (generated by
`scripts/generate_legacy_entity_map.py` from a local, gitignored copy of that
package's `modbus_sungrow.yaml` -- see `dev/legacy_reference/README.md`) is
the field-by-field cross-reference the config flow reads to know which legacy
`entity_id` to claim for a given field, matched by `(register_space, address)`
since both projects use the same protocol addresses. The generator also
asserts unit/device_class/state_class parity between the two on every match:
a mismatch there doesn't crash anything, it silently freezes long-term
statistics (see `unit_mapping.py`'s `state_class_for` -- daily counters need
`total_increasing` since they reset each day, lifetime counters need plain
`total`, backwards until this was caught by the generator).

Every install goes through two config-flow steps after the connection step:
`async_step_migrating` ("are you migrating from the legacy YAML package?" --
a plain yes/no, not stored in the entry, it only routes whether the second
step shows at all) and, if yes, `async_step_legacy_naming` (keep the legacy
package's flat `entity_id`s, recommended only when replacing an existing
YAML install to keep its automations/dashboards working, or this
integration's modern device-prefixed ones, the default). **This choice is
made once and is permanent** -- there is no options flow or reconfigure step
for it, and none should be added; changing it means removing and re-adding
the integration. `async_step_legacy_naming` also hard-blocks (a red
`legacy_entities_active` form error, not just a warning) submitting "keep
legacy ids" while any of those ids are still live in the entity registry --
claiming would otherwise silently land on `sensor.foo_2` instead of
`sensor.foo`, defeating the entire point. Choosing modern ids is never
blocked, since nothing is being claimed in that case. It works by setting
`self.entity_id`
directly in `SungrowEntity.__init__` (`entity.py`) when
`legacy_naming.suggested_object_id_for(key, platform)` finds a same-domain
match -- **not** `_attr_suggested_object_id`, which looks like the obvious
API but is backed by a hard-coded read-only `Entity.suggested_object_id`
property that ignores `_attr_*` overrides entirely. Setting `entity_id`
itself is the one path HA's entity platform treats as "this entity supplies
its own id," which is also the only path that skips `has_entity_name`'s
automatic device-name prefixing. `unique_id` is left untouched either way --
HA's recorder history is keyed by `entity_id`, not `unique_id`, so there's no
need to make the two integrations' unique ids agree.

The three fields where the legacy package exposes both a raw diagnostic
sensor and a switch for the same register (`controls_backup_mode_enabled`
and friends) only ever get a `switch` entity here, so the lookup is
domain-aware and simply never claims the orphaned sensor's id -- a deliberate
scope limit, not a gap. `binary_sensor.py`'s and `button.py`'s entities are
hand-authored computed/action keys with no `iter_fields()` counterpart, so
their legacy equivalents are a small manual override table in the generator
script (`_MANUAL_LEGACY_OVERRIDES`), not address-matched.

`config/integrations/legacy_migration_package.yaml` is a redacted copy of
that YAML package (as a `homeassistant: packages:` include in
`config/configuration.yaml`, in a sibling `integrations/` folder matching
mkaiser's own install docs), for running it side by side with a `sungrow`
config entry in the dev container while testing migration. **Its `modbus:`
hub opens its own independent TCP connection** -- HA's legacy YAML Modbus
platform (still fully supported, no deprecation, as of HA 2026.9.0) does not
share a connection with the new pooled `async_get_unit` registry this
integration uses, even against the same host:port. Running both continuously
against the same physical inverter means two competing sessions; fine for
brief side-by-side comparison, not for leaving both enabled long-term. To
actually test a migration, remove/disable the legacy package and restart HA
first -- an entity_id can't be claimed out from under a still-live entity
holding it. Restarting stops HA recreating those entities but does not
delete their existing registry rows; if any remain (Settings → Devices &
Services → Entities, filter by the `modbus`/`template` integrations) the
`legacy_naming` step's hard block will catch it and say so.

## Conventions

- Config is UI-only (config flow), no YAML setup.
- The HA-facing identity (domain `sungrow`, manifest/HACS display name "Sungrow") is deliberately broader than the vendored library's `SungrowSHx`/`sungrow_modbus` naming, which stays scoped to the SHx (SH-RS/SH-RT/SHT) register map it actually implements today -- don't rename the library to match if the domain or display name changes again.
- `sungrow_modbus/` keeps its own vendored formatting/lint posture (excluded from the house ruff config) since it mirrors an upstream package -- don't reformat it to match the rest of the repo.
- When a register is technically writable but unsafe/meaningless to expose as a raw control in HA, mark it in `field_index.py`'s `_READ_ONLY_OVERRIDE` rather than special-casing it in a platform module.
