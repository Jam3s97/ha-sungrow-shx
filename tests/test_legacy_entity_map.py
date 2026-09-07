"""
Guard rails for custom_components/sungrow/legacy_entity_map.json.

Skipped unless dev/legacy_reference/modbus_sungrow.yaml is present locally
(see dev/legacy_reference/README.md) -- it's a gitignored build input, not
something CI has, so these tests are a local/manual check, not a CI gate.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
LEGACY_YAML = ROOT / "dev" / "legacy_reference" / "modbus_sungrow.yaml"
GENERATOR = ROOT / "scripts" / "generate_legacy_entity_map.py"
OUTPUT = ROOT / "custom_components" / "sungrow" / "legacy_entity_map.json"

pytestmark = pytest.mark.skipif(
    not LEGACY_YAML.exists(),
    reason=f"{LEGACY_YAML} not present -- see dev/legacy_reference/README.md",
)


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "generate_legacy_entity_map", GENERATOR
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_no_unit_mismatches() -> None:
    """No unacknowledged unit/device_class/state_class mismatch survives."""
    generator = _load_generator()
    _entity_map, coverage = generator.build_map()
    assert coverage.unit_mismatches == []


def test_committed_json_is_up_to_date() -> None:
    """The committed legacy_entity_map.json matches a fresh generator run."""
    generator = _load_generator()
    entity_map, _coverage = generator.build_map()
    rendered = json.dumps(entity_map, indent=2, sort_keys=True) + "\n"
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    assert current == rendered, (
        "run scripts/generate_legacy_entity_map.py to refresh it"
    )
