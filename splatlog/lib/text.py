from __future__ import annotations
import dataclasses
from functools import wraps
from inspect import isclass
import typing
from typing import (
    Any,
    ForwardRef,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)
import types
from collections import abc

from splatlog.lib.collections import partition_mapping

BUILTINS_MODULE = object.__module__
TYPING_MODULE = typing.__name__


def is_typing(x: Any) -> bool:
    return get_origin(x) or get_args(x) or type(x).__module__ == TYPING_MODULE


FmtOptsSelf = TypeVar("FmtOptsSelf", bound="FmtOpts")


@dataclasses.dataclass(frozen=True)
class FmtOpts:
    @classmethod
    def of(cls, x) -> FmtOptsSelf:
        if x is None:
            return cls()
        if isinstance(x, cls):
            return x
        return cls(**x)

    @classmethod
    def provide(cls, fn):
        field_names = {field.name for field in dataclasses.fields(cls)}

        @wraps(fn)
        def wrapped(*args, **kwds):
            field_kwds, fn_kwds = partition_mapping(kwds, field_names)
            if isinstance(args[-1], cls):
                *args, instance = args
                if field_kwds:
                    instance = dataclasses.replace(instance, **field_kwds)
            elif field_kwds:
                instance = cls(**field_kwds)
            else:
                instance = DEFAULT_FMT_OPTS

            return fn(*args, instance, **fn_kwds)

        return wrapped

    module_names: bool = True


DEFAULT_FMT_OPTS = FmtOpts()


@FmtOpts.provide
def fmt(x: Any, opts: FmtOpts) -> str:
    if is_typing(x):
        return fmt_type_hint(x, opts)

    if isinstance(x, type):
        return fmt_type(x, opts)

    return repr(x)


@FmtOpts.provide
def fmt_type(t: Type, opts: FmtOpts) -> str:
    """
    ##### Examples #####

    ```python
    >>> fmt_type(abc.Collection)
    'collections.abc.Collection'

    >>> fmt_type(abc.Collection, module_names=False)
    'Collection'

    >>> fmt_type(abc.Collection, FmtOpts(module_names=False))
    'Collection'

    >>> fmt_type(abc.Collection, FmtOpts(module_names=False), module_names=True)
    'collections.abc.Collection'

    ```
    """

    if opts.module_names and t.__module__ != BUILTINS_MODULE:
        return f"{t.__module__}.{t.__qualname__}"
    return t.__qualname__


def _nest(formatted: str, nested: bool) -> str:
    return f"({formatted})" if nested else formatted


@FmtOpts.provide
def _fmt_optional(t: Any, opts: FmtOpts, *, nested: bool = False) -> str:
    if get_origin(t) is Literal:
        return _nest("None | " + fmt_type_hint(t, opts), nested)
    return fmt_type_hint(t, opts, nested=True) + "?"


@FmtOpts.provide
def fmt_type_hint(t: Any, opts: FmtOpts, *, nested: bool = False) -> str:
    """
    ##### Examples #####

    Examples can be found in <doc/splatlog/lib/text/fmt_type_hint.md>.

    """

    if t is Ellipsis:
        return "..."

    if t is types.NoneType:
        return "None"

    if isinstance(t, ForwardRef):
        return t.__forward_arg__

    if isinstance(t, TypeVar):
        # NOTE  Just gonna punt on this for now... for some reason the way
        #       Python handles generics just manages to frustrate and confuse
        #       me...
        return repr(t)

    origin = get_origin(t)
    args = get_args(t)

    if args == ():
        return fmt_type(origin or t, opts)

    if origin is Union:
        if len(args) == 2:
            if args[0] is types.NoneType:
                return _fmt_optional(args[1], opts, nested=nested)
            if args[1] is types.NoneType:
                return _fmt_optional(args[0], opts, nested=nested)

        return _nest(
            " | ".join(
                fmt_type_hint(
                    arg, opts, nested=(get_origin(arg) is not Literal)
                )
                for arg in args
            ),
            nested,
        )

    if origin is Literal:
        return _nest(" | ".join(fmt(arg) for arg in args), nested)

    if origin is dict:
        return (
            "{"
            + fmt_type_hint(args[0], opts, nested=True)
            + ": "
            + fmt_type_hint(args[1], opts, nested=True)
            + "}"
        )

    if origin is list:
        return fmt_type_hint(args[0], opts, nested=True) + "[]"

    if origin is tuple:
        return "(" + ", ".join(fmt_type_hint(arg, opts) for arg in args) + ")"

    if origin is set:
        return "{" + fmt_type_hint(args[0], opts) + "}"

    if origin is abc.Callable:
        return _nest(
            "("
            + ", ".join(fmt_type_hint(arg, opts) for arg in args[0])
            + ") -> "
            + fmt_type_hint(args[1], opts),
            nested,
        )

    return typing._type_repr(t)


def short_name(x: Any) -> Optional[str]:
    name = getattr(x, "__qualname__", None)
    if isinstance(name, str):
        return name
    name = getattr(x, "__name__", None)
    if isinstance(name, str):
        return name
    return None


def full_name(x: Any) -> Optional[str]:
    """
    ##### Examples #####

    ```python

    >>> full_name(str)
    'str'

    >>> full_name(Any)
    'typing.Any'

    >>> class A:
    ...     pass

    >>> full_name(A)
    'splatlog.lib.text.A'

    >>> import inspect

    >>> full_name(inspect.isfunction)
    'inspect.isfunction'

    >>> full_name(inspect) is None
    True

    >>> class Screwy:
    ...     def __init__(self, name):
    ...         self.__qualname__ = name

    >>> full_name(Screwy(123)) is None
    True

    >>> full_name(Screwy("Louie"))
    'splatlog.lib.text.Louie'

    ```
    """

    if (
        (module := getattr(x, "__module__", None))
        and isinstance(module, str)
        and (name := short_name(x))
    ):
        if module != BUILTINS_MODULE:
            return f"{module}.{name}"
        return name
