"""Backup / off-grid output port telemetry."""

from __future__ import annotations

from ..data_model import SungrowComponent, int16, int32_word_swapped


class BackupPower(SungrowComponent):
    """Power delivered to the backup (EPS) output (input registers)."""

    register_space = "input"

    phase_a_power = int16(5722, unit="W", category="backup")
    phase_b_power = int16(5723, unit="W", category="backup")
    phase_c_power = int16(5724, unit="W", category="backup")
    total_power = int32_word_swapped(5725, unit="W", category="backup")
