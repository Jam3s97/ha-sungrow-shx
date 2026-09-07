"""Address helpers for Sungrow register references.

Sungrow's own documentation (and the community-maintained register map this
library is built from) already lists addresses as zero-based Modbus protocol
addresses -- the same addresses ``pymodbus``/``tmodbus``/``modbus-connection``
expect on the wire. Vendor "register number" columns some spec sheets print
are simply ``address + 1`` (a one-based, human-facing counting convention).

This module keeps that distinction explicit so field declarations can be
cross-checked against Sungrow's published register tables without silently
mixing the two numbering schemes.
"""

from __future__ import annotations


def register_address(register_number: int) -> int:
    """Return the zero-based protocol address for a one-based register number.

    Example: register number 5001 (as printed in Sungrow's register map)
    lives at protocol address 5000.
    """
    if register_number < 1:
        raise ValueError(f"Invalid Sungrow register number: {register_number}")
    return register_number - 1


def register_number(address: int) -> int:
    """Return the one-based register number for a zero-based protocol address."""
    if address < 0:
        raise ValueError(f"Invalid Sungrow protocol address: {address}")
    return address + 1
