# Legacy YAML reference

`modbus_sungrow.yaml` in this directory is a local build input for
`scripts/generate_legacy_entity_map.py`, trimmed to the `modbus.sensors` /
`modbus.switches` blocks the generator actually reads (register address,
`input_type`, `unit_of_measurement`, `device_class`, `state_class`,
`unique_id`, `name`). It is **not tracked in git** — see `.gitignore`.

It comes from
[mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant](https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant),
the long-running YAML Modbus package this integration is meant to offer a
migration path from. That repo is the canonical source — if you need to
refresh this file (a new register was added upstream, a unit changed), pull
the current `modbus_sungrow.yaml` from `main` there, not from here.

The `custom_components/sungrow/legacy_entity_map.json` this generator
produces *is* committed — that's the derived, factual (address → entity_id /
unit / device_class) mapping the integration needs at runtime, as opposed to
mkaiser's file itself, which stays local.
