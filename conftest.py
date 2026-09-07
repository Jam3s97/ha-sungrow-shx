"""
Root conftest.

Its only job is to exist here: pytest adds the directory of every conftest.py
it collects to ``sys.path`` (when that directory has no ``__init__.py``), and
the integration under test is imported as ``custom_components.sungrow`` --
the same way Home Assistant itself imports it -- so this repo root, not
``tests/``, needs to be on the path.
"""

from __future__ import annotations
