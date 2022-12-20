from __future__ import annotations
from typing import (
    Any,
    Iterable,
    Iterator,
    Optional,
    TypeGuard,
    TypeVar,
    Union,
    Type,
    cast,
)
from inspect import isclass, isroutine
from collections.abc import Mapping

from rich.table import Table, Column
from rich.padding import PaddingDimensions
from rich.box import Box
from rich.theme import Theme
from rich.pretty import Pretty
from rich.highlighter import ReprHighlighter
from rich.columns import Columns
from rich.text import Text

from splatlog.lib.text import fmt_routine, BUILTINS_MODULE

from .constants import THEME
from .typings import is_rich
from .enrich import enrich, enrich_type, enrich_type_of

TableSource = Union[Mapping[str, object], Iterable[tuple[str, object]]]


def ntv_table(
    source: TableSource,
    *headers: Union[Column, str],
    box: Optional[Box] = None,
    padding: PaddingDimensions = (0, 1),
    collapse_padding: bool = True,
    show_header: bool = False,
    show_footer: bool = False,
    show_edge: bool = False,
    pad_edge: bool = False,
    sort: bool = False,
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
        table.add_column(
            "Name", style=THEME.styles["log.data.name"], min_width=10
        )
        # table.add_column("Type", style=THEME.styles["log.data.type"])
        table.add_column("Type", min_width=10, max_width=40)
        table.add_column("Value", min_width=10)

    items = (
        # I think `cast` is needed here because `Mapping[str, object` and
        # `Iterable[tuple[str, object]]` actually overlap, as `Mapping` is an
        # `Iterable` over its keys, introducing a weird
        # `Iterable[tuple[str, object], Unknown]` type when left to it's own
        # devices
        cast(Iterable[tuple[str, object]], source.items())
        if isinstance(source, Mapping)
        else source
    )

    for key, value in items:
        if is_rich(value) and value.__class__.__module__.startswith("rich."):
            rich_value_type = None
            rich_value = value
        elif isclass(value):
            rich_value_type = None
            rich_value = enrich_type(value)
        else:
            rich_value_type = enrich_type_of(value)
            rich_value = enrich(value)
        table.add_row(key, rich_value_type, rich_value)
    return table
