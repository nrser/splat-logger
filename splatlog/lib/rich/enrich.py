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

from .enriched_type import EnrichedType
from .typings import is_rich


REPR_HIGHLIGHTER = ReprHighlighter()


def repr_highlight(value: object) -> Text:
    return REPR_HIGHLIGHTER(repr(value))


def enrich_type(typ: Type[object]) -> RenderableType:
    if hasattr(typ, "__rich_type__"):
        return typ.__rich_type__()
    return EnrichedType(typ)


def enrich_type_of(value: object) -> RenderableType:
    return enrich_type(type(value))


def enrich(value: object, inline: bool = False) -> RenderableType:
    if is_rich(value) and (inline is False or isinstance(value, Text)):
        return value

    if isinstance(value, str):
        if all(c.isprintable() or c.isspace() for c in value):
            return value
        else:
            return repr_highlight(value)

    fallback = repr_highlight if inline else Pretty

    if isclass(value):
        return enrich_type(value)

    if isroutine(value):
        return fmt_routine(value, fallback=fallback)

    return fallback(value)
