"""
Helpers for working with [rich][]

[rich]: https://pypi.org/project/rich/
"""

from __future__ import annotations
from typing import Any, Optional, TypeGuard, Union, Type
from inspect import isfunction, isroutine
from collections.abc import Mapping

from rich.table import Table, Column
from rich.padding import PaddingDimensions
from rich.box import Box
from rich.console import Console, ConsoleRenderable, RichCast
from rich.theme import Theme
from rich.pretty import Pretty
from rich.highlighter import ReprHighlighter

from splatlog.lib.text import fmt_type, fmt_routine


THEME = Theme(
    {
        "log.level": "bold",
        "log.name": "dim blue",
        "log.label": "dim white",
        "log.data.name": "italic blue",
        "log.data.type": "italic #4ec9b0",
    }
)

DEFAULT_CONSOLE = Console(theme=THEME)


# An object that "is Rich".
TRich = Union[ConsoleRenderable, RichCast]

# An object that is ready for Rich printing: either a `str` or `TRich`
TEnriched = Union[str, TRich]

repr_highlight = ReprHighlighter()


def is_rich(x: Any) -> TypeGuard[TRich]:
    return isinstance(x, (ConsoleRenderable, RichCast))


def capture_riches(
    *objects: Any, console: Console = DEFAULT_CONSOLE, **print_kwds
) -> str:
    with console.capture() as capture:
        console.print(*objects, **print_kwds)
    return capture.get()


def enrich_type(typ: Type) -> TEnriched:
    return fmt_type(typ, fallback=Pretty)


def enrich_type_of(value: Any) -> Union[str, TRich]:
    return enrich_type(type(value))


def enrich(value: Any) -> Union[str, TRich]:
    if isinstance(value, str):
        if all(c.isprintable() or c.isspace() for c in value):
            return value
        else:
            return Pretty(value)

    if isroutine(value):
        return fmt_routine(value, fallback=Pretty)

    return Pretty(value)


def ntv_table(
    mapping: Mapping,
    *headers: Union[Column, str],
    box: Optional[Box] = None,
    padding: PaddingDimensions = (0, 1),
    collapse_padding: bool = True,
    show_header: bool = False,
    show_footer: bool = False,
    show_edge: bool = False,
    pad_edge: bool = False,
    **kwds,
) -> Table:
    table = Table(
        *headers,
        box=box,
        padding=padding,
        collapse_padding=collapse_padding,
        show_header=show_header,
        show_footer=show_footer,
        show_edge=show_edge,
        pad_edge=pad_edge,
        **kwds,
    )
    if len(headers) == 0:
        table.add_column("Name", style=THEME.styles["log.data.name"])
        table.add_column("Type", style=THEME.styles["log.data.type"])
        table.add_column("Value")
    for key in sorted(mapping.keys()):
        value = mapping[key]
        if is_rich(value):
            rich_value_type = None
            rich_value = value
        else:
            rich_value_type = enrich_type_of(value)
            if isinstance(value, str):
                rich_value = value
            elif (
                isfunction(value)
                and hasattr(value, "__module__")
                and hasattr(value, "__name__")
            ):
                rich_value = ReprHighlighter()(
                    f"<function {value.__module__}.{value.__name__}>"
                )
            else:
                rich_value = Pretty(value)
        table.add_row(key, rich_value_type, rich_value)
    return table
