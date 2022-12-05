"""
Helpers for working with [rich][]

[rich]: https://pypi.org/project/rich/
"""

from __future__ import annotations
from typing import Any, Optional, TypeGuard, TypeVar, Union, Type
from inspect import isclass, isfunction, isroutine
from collections.abc import Mapping
from collections import UserList

from rich.table import Table, Column
from rich.padding import PaddingDimensions
from rich.box import Box
from rich.console import (
    Console,
    ConsoleRenderable,
    RichCast,
    ConsoleOptions,
    RenderResult,
    RenderableType,
)
from rich.theme import Theme
from rich.pretty import Pretty
from rich.highlighter import ReprHighlighter
from rich.columns import Columns
from rich.segment import Segment
from rich.text import Text

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
Rich = Union[ConsoleRenderable, RichCast]

repr_highlight = ReprHighlighter()

_EnrichedSelf = TypeVar("_EnrichedSelf", bound="Enriched")


class Enriched(tuple):
    def __new__(self, *values) -> _EnrichedSelf:
        return tuple.__new__(Enriched, values)

    def __str__(self) -> str:
        return " ".join(str(item) for item in self)

    # def __rich_console__(
    #     self, console: Console, options: ConsoleOptions
    # ) -> RenderableType:

    def __rich__(self):
        return Columns(enrich(item) for item in self)


def is_rich(x: object) -> TypeGuard[Rich]:
    """
    Is an object "rich"? This amounts to:

    1.  Fullfilling one of the protocols:
        -   `rich.console.ConsoleRenderable` — having a `__rich_console__`
            method, the signature of which is:

            ```python
            def __rich_console__(
                self,
                console: rich.console.Console,
                options: rich.console.ConsoleOptions
            ) -> rich.console.RenderResult:
                ...
            ```

        -   `rich.console.RichCast` — having a `__rich__ method, the signature
            of which is:

            ```python
            def __rich__(self) -> rich.console.RenderableType:
                ...
            ```

    2.  **_Not_** being a class (tested with `inspect.isclass`).

        This check is applied a few places in the Rich rendering code, and is
        there because a simple check like

        ```python
        hasattr(renderable, "__rich_console__")
        ```

        is used to test if an object fullfills the protocols from (1). Those
        attributes are assumed to be _instance methods_, which show up as
        attributes on the class objects as well.

        The additional

        ```python
        not isclass(renderable)
        ```

        check prevents erroneously calling those instance methods on the class
        objects.
    """
    return isinstance(x, (ConsoleRenderable, RichCast)) and not isclass(x)


def capture_riches(
    *objects: Any, console: Console = DEFAULT_CONSOLE, **print_kwds
) -> str:
    with console.capture() as capture:
        console.print(*objects, **print_kwds)
    return capture.get()


def enrich_type(typ: Type) -> RenderableType:
    return Text(fmt_type(typ), style="inspect.class")


def enrich_type_of(value: Any) -> RenderableType:
    return enrich_type(type(value))


def enrich(value: object) -> RenderableType:
    if is_rich(value):
        return value

    if isinstance(value, str):
        if all(c.isprintable() or c.isspace() for c in value):
            return value
        else:
            return Pretty(value)

    if isclass(value):
        return enrich_type(value)

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
            rich_value = enrich(value)
        table.add_row(key, rich_value_type, rich_value)
    return table
