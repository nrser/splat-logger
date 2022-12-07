"""
Helpers for working with [rich][]

[rich]: https://pypi.org/project/rich/
"""

from __future__ import annotations
from typing import Any, Optional, TypeGuard, TypeVar, Union, Type
from inspect import isclass, isroutine
from collections.abc import Mapping

from rich.table import Table, Column
from rich.padding import PaddingDimensions
from rich.box import Box
from rich.console import (
    Console,
    ConsoleRenderable,
    RichCast,
    RenderableType,
)
from rich.theme import Theme
from rich.pretty import Pretty
from rich.highlighter import ReprHighlighter
from rich.columns import Columns
from rich.text import Text

from splatlog.lib.text import fmt_routine, BUILTINS_MODULE

from .constants import THEME, DEFAULT_CONSOLE
from .typings import Rich, is_rich
from .enriched_type import EnrichedType
from .ntv_table import ntv_table
from .enrich import REPR_HIGHLIGHTER, enrich, enrich_type, enrich_type_of

_InlineSelf = TypeVar("_InlineSelf", bound="Inline")


class Inline(tuple):
    def __new__(self, *values) -> _InlineSelf:
        return tuple.__new__(Inline, values)

    def __str__(self) -> str:
        return " ".join(
            (entry if isinstance(entry, str) else repr(entry)) for entry in self
        )

    def __rich__(self):
        text = Text()
        for index, entry in enumerate(self):
            if index != 0:
                text.append(" ")
            if isinstance(entry, str):
                text.append(entry)
            else:
                text.append(enrich(entry, inline=True))
        return text


def capture_riches(
    *objects: Any, console: Console = DEFAULT_CONSOLE, **print_kwds
) -> str:
    with console.capture() as capture:
        console.print(*objects, **print_kwds)
    return capture.get()
