#!/usr/bin/env python3
"""
Cross-reference this integration's registers against mkaiser's legacy YAML.

Reads the ``modbus.sensors``/``modbus.switches`` entries of a local copy of
`mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant`'s ``modbus_sungrow.yaml``
(see ``dev/legacy_reference/README.md``), matches them against every field
declared in ``sungrow_modbus`` by protocol address, and writes
``custom_components/sungrow/legacy_entity_map.json`` -- the artifact a future
config-flow migration step reads to know which legacy ``entity_id`` to claim
for a given field.

Usage::

    scripts/generate_legacy_entity_map.py          # regenerate the JSON
    scripts/generate_legacy_entity_map.py --check  # exit 1 if it's stale
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from homeassistant.util import slugify as ha_slugify

ROOT = Path(__file__).resolve().parent.parent
CUSTOM_COMPONENTS = ROOT / "custom_components"
LEGACY_YAML = ROOT / "dev" / "legacy_reference" / "modbus_sungrow.yaml"
OUTPUT = CUSTOM_COMPONENTS / "sungrow" / "legacy_entity_map.json"

sys.path.insert(0, str(CUSTOM_COMPONENTS))

from sungrow.field_index import FieldRef, iter_fields  # noqa: E402
from sungrow.sungrow_modbus import SungrowSHx  # noqa: E402
from sungrow.unit_mapping import (  # noqa: E402
    native_unit_and_device_class,
    state_class_for,
)

# Mismatches reviewed and deliberately left as-is, with why -- not swept under
# the rug, but not blocking either. Anything not listed here still fails the
# check, so this isn't a general escape hatch.
_ACKNOWLEDGED_MISMATCHES: dict[str, str] = {
    "status_reactive_power": (
        "legacy declares unit W / device_class power for a var value -- a "
        "bug in the legacy file itself, not something to copy"
    ),
    "battery_capacity_high_precision": (
        "legacy uses device_class energy_storage (a capacity gauge, not a "
        "meter); this repo's unit_mapping.py maps every kWh field to plain "
        "ENERGY today -- open design question, not fixed here"
    ),
}


class _LegacyLoader(yaml.SafeLoader):
    """
    A YAML loader tolerant of the legacy package's ``!secret`` tag.

    We only need the document's structure, never the actual secret values.
    """


_LegacyLoader.add_constructor(
    "!secret", lambda loader, node: f"!secret {loader.construct_scalar(node)}"
)


@dataclass(frozen=True)
class LegacyCandidate:
    """One legacy entity (from ``sensors:`` or ``switches:``) at a given address."""

    domain: str
    entity_id: str
    unique_id: str | None
    unit_of_measurement: str | None
    device_class: str | None
    state_class: str | None

    def as_dict(self) -> dict[str, Any]:
        """Render as a plain dict, for JSON output."""
        return {
            "domain": self.domain,
            "entity_id": self.entity_id,
            "unique_id": self.unique_id,
            "unit_of_measurement": self.unit_of_measurement,
            "device_class": self.device_class,
            "state_class": self.state_class,
        }


@dataclass
class Coverage:
    """Tallies surfaced as a human-readable report, not part of the JSON output."""

    matched_unique: list[str] = field(default_factory=list)
    matched_ambiguous: dict[str, list[LegacyCandidate]] = field(default_factory=dict)
    device_only: list[str] = field(default_factory=list)
    legacy_only: list[LegacyCandidate] = field(default_factory=list)
    unit_mismatches: list[str] = field(default_factory=list)
    acknowledged_mismatches: list[str] = field(default_factory=list)


def _slugify(name: str) -> str:
    """
    Reproduce Home Assistant's entity-id slugging closely enough to match it.

    Delegates to HA's own ``slugify`` so the derived legacy ``entity_id``
    exactly matches what the ``modbus``/``template`` YAML platforms would
    have generated for the same ``name:``.
    """
    return ha_slugify(name)


def _load_legacy_yaml() -> dict[str, Any]:
    if not LEGACY_YAML.exists():
        msg = (
            f"{LEGACY_YAML} not found -- see dev/legacy_reference/README.md "
            "for where to get it."
        )
        raise SystemExit(msg)
    with LEGACY_YAML.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_LegacyLoader)  # noqa: S506


def _legacy_candidates(
    document: dict[str, Any],
) -> dict[tuple[str, int], list[LegacyCandidate]]:
    """Index every legacy sensor/switch entry by ``(register_space, address)``."""
    hub = document["modbus"][0]
    index: dict[tuple[str, int], list[LegacyCandidate]] = {}

    for entry in hub.get("sensors", []):
        key = (entry["input_type"], int(entry["address"]))
        candidate = LegacyCandidate(
            domain="sensor",
            entity_id=entry.get("entity_id") or f"sensor.{_slugify(entry['name'])}",
            unique_id=entry.get("unique_id"),
            unit_of_measurement=entry.get("unit_of_measurement"),
            device_class=entry.get("device_class"),
            state_class=entry.get("state_class"),
        )
        index.setdefault(key, []).append(candidate)

    for entry in hub.get("switches", []):
        key = (entry.get("write_type", "holding"), int(entry["address"]))
        candidate = LegacyCandidate(
            domain="switch",
            entity_id=entry.get("entity_id") or f"switch.{_slugify(entry['name'])}",
            unique_id=entry.get("unique_id"),
            unit_of_measurement=None,
            device_class=None,
            state_class=None,
        )
        index.setdefault(key, []).append(candidate)

    return index


def _device_register_space(device: SungrowSHx, component_name: str) -> str:
    component = getattr(device, component_name)
    return type(component).register_space


def _check_unit_match(
    field_ref: FieldRef, candidate: LegacyCandidate, coverage: Coverage
) -> None:
    unit, device_class = native_unit_and_device_class(field_ref)
    state_class = state_class_for(field_ref)

    device_class_str = device_class.value if device_class else None
    state_class_str = state_class.value if state_class else None

    mismatches = []
    if candidate.unit_of_measurement and unit and candidate.unit_of_measurement != unit:
        mismatches.append(f"unit {candidate.unit_of_measurement!r} != {unit!r}")
    if (
        candidate.device_class
        and device_class_str
        and candidate.device_class != device_class_str
    ):
        mismatches.append(
            f"device_class {candidate.device_class!r} != {device_class_str!r}"
        )
    if (
        candidate.state_class
        and state_class_str
        and candidate.state_class != state_class_str
    ):
        mismatches.append(
            f"state_class {candidate.state_class!r} != {state_class_str!r}"
        )

    if not mismatches:
        return
    line = f"{field_ref.key}: {'; '.join(mismatches)}"
    if field_ref.key in _ACKNOWLEDGED_MISMATCHES:
        coverage.acknowledged_mismatches.append(
            f"{line} -- {_ACKNOWLEDGED_MISMATCHES[field_ref.key]}"
        )
    else:
        coverage.unit_mismatches.append(line)


def build_map() -> tuple[dict[str, list[dict[str, Any]]], Coverage]:
    """Match every declared device field against the legacy YAML, by address."""
    document = _load_legacy_yaml()
    legacy_index = _legacy_candidates(document)
    remaining_legacy = {
        key: list(candidates) for key, candidates in legacy_index.items()
    }

    device = SungrowSHx(object())  # pure introspection -- no I/O ever happens
    result: dict[str, list[dict[str, Any]]] = {}
    coverage = Coverage()

    for field_ref in iter_fields(device):
        metadata = field_ref.metadata
        if metadata.register_number is None:
            coverage.device_only.append(field_ref.key)
            continue
        address = metadata.register_number - 1
        register_space = _device_register_space(device, field_ref.component)
        key = (register_space, address)
        candidates = legacy_index.get(key)

        if not candidates:
            coverage.device_only.append(field_ref.key)
            continue

        result[field_ref.key] = [candidate.as_dict() for candidate in candidates]
        remaining_legacy.pop(key, None)

        if len(candidates) == 1:
            coverage.matched_unique.append(field_ref.key)
        else:
            coverage.matched_ambiguous[field_ref.key] = candidates

        if metadata.value_kind == "number" and len(candidates) == 1:
            _check_unit_match(field_ref, candidates[0], coverage)

    for candidates in remaining_legacy.values():
        coverage.legacy_only.extend(candidates)

    return result, coverage


def _print_coverage(coverage: Coverage) -> None:
    print(f"matched (unique):    {len(coverage.matched_unique)}", file=sys.stderr)
    print(f"matched (ambiguous): {len(coverage.matched_ambiguous)}", file=sys.stderr)
    for key, candidates in coverage.matched_ambiguous.items():
        ids = ", ".join(c.entity_id for c in candidates)
        print(f"  {key}: {ids}", file=sys.stderr)
    print(f"device-only fields:   {len(coverage.device_only)}", file=sys.stderr)
    print(f"legacy-only entries:  {len(coverage.legacy_only)}", file=sys.stderr)
    for candidate in coverage.legacy_only:
        print(f"  {candidate.entity_id}", file=sys.stderr)
    print(f"unit/class mismatches: {len(coverage.unit_mismatches)}", file=sys.stderr)
    for line in coverage.unit_mismatches:
        print(f"  {line}", file=sys.stderr)
    print(
        f"acknowledged mismatches: {len(coverage.acknowledged_mismatches)}",
        file=sys.stderr,
    )
    for line in coverage.acknowledged_mismatches:
        print(f"  {line}", file=sys.stderr)


def main() -> int:
    """Regenerate (or, with ``--check``, verify) ``legacy_entity_map.json``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed JSON is stale, without writing it",
    )
    args = parser.parse_args()

    entity_map, coverage = build_map()
    _print_coverage(coverage)

    if coverage.unit_mismatches:
        print(
            "error: unit/device_class/state_class mismatches found -- "
            "these silently freeze long-term statistics if shipped, see above",
            file=sys.stderr,
        )
        return 1

    rendered = json.dumps(entity_map, indent=2, sort_keys=True) + "\n"

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(
                f"error: {OUTPUT} is stale, run without --check to regenerate",
                file=sys.stderr,
            )
            return 1
        print("legacy_entity_map.json is up to date", file=sys.stderr)
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
