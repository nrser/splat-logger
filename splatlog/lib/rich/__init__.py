"""
Helpers for working with [rich][]

[rich]: https://pypi.org/project/rich/
"""

from __future__ import annotations
from typing import Any

from rich.console import Console

# Re-exports
from .constants import THEME, DEFAULT_CONSOLE
from .typings import Rich, is_rich
from .enriched_type import EnrichedType
from .ntv_table import ntv_table
from .enrich import REPR_HIGHLIGHTER, enrich, enrich_type, enrich_type_of
from .inline import Inline


def capture_riches(
    *objects: Any, console: Console = DEFAULT_CONSOLE, **print_kwds
) -> str:
    with console.capture() as capture:
        console.print(*objects, **print_kwds)
    return capture.get()
