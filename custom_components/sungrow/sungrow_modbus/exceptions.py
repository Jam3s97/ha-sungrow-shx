"""Sungrow-modbus exceptions."""

from __future__ import annotations


class SungrowError(Exception):
    """Base class for errors raised by this library."""


class SungrowValueValidationError(SungrowError):
    """A value rejected by a field's write validation."""
