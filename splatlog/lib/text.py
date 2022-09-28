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

BUILTINS_MODULE = object.__module__
TYPING_MODULE = typing.__name__


def is_typing(x: Any) -> bool:
    return get_origin(x) or get_args(x) or type(x).__module__ == TYPING_MODULE


def fmt(x: Any) -> str:
    if is_typing(x):
        return fmt_type_hint(x)

    if isinstance(x, type):
        return fmt_type(x)

    return repr(x)


def fmt_type(t: Type, *, full_names: bool = True) -> str:
    if full_names and t.__module__ != BUILTINS_MODULE:
        return f"{t.__module__}.{t.__qualname__}"
    return t.__qualname__


def _nest(formatted: str, nested: bool) -> str:
    return f"({formatted})" if nested else formatted


def _fmt_optional(t: Any, *, nested: bool = False) -> str:
    if get_origin(t) is Literal:
        return _nest("None | " + fmt_type_hint(t), nested)
    return fmt_type_hint(t, nested=True) + "?"


def fmt_type_hint(t: Any, *, nested: bool = False) -> str:
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
        return fmt_type(origin or t)

    if origin is Union:
        if len(args) == 2:
            if args[0] is types.NoneType:
                return _fmt_optional(args[1], nested=nested)
            if args[1] is types.NoneType:
                return _fmt_optional(args[0], nested=nested)

        return _nest(
            " | ".join(
                fmt_type_hint(arg, nested=(get_origin(arg) is not Literal))
                for arg in args
            ),
            nested,
        )

    if origin is Literal:
        return _nest(" | ".join(fmt(arg) for arg in args), nested)

    if origin is dict:
        return (
            "{"
            + fmt_type_hint(args[0], nested=True)
            + ": "
            + fmt_type_hint(args[1], nested=True)
            + "}"
        )

    if origin is list:
        return fmt_type_hint(args[0], nested=True) + "[]"

    if origin is tuple:
        return "(" + ", ".join(fmt_type_hint(arg) for arg in args) + ")"

    if origin is set:
        return "{" + fmt_type_hint(args[0]) + "}"

    if origin is abc.Callable:
        return _nest(
            "("
            + ", ".join(fmt_type_hint(arg) for arg in args[0])
            + ") -> "
            + fmt_type_hint(args[1]),
            nested,
        )

    return typing._type_repr(t)


def get_type_name(type_: Any) -> str:

    name = (
        getattr(type_, "__name__", None)
        or getattr(type_, "_name", None)
        or getattr(type_, "__forward_arg__", None)
    )
    if name is None:
        origin = getattr(type_, "__origin__", None)
        name = getattr(origin, "_name", None)
        if name is None and not isclass(type_):
            return get_type_name(type(type_))

    args = getattr(type_, "__args__", ()) or getattr(type_, "__values__", ())

    if args:
        if name == "Literal":
            name = " | ".join(repr(arg) for arg in args)
        elif name == "Union":
            name = " | ".join(get_type_name(arg) for arg in args)
        else:
            formatted_args = ", ".join(get_type_name(arg) for arg in args)
            name = "{}[{}]".format(name, formatted_args)

    module = getattr(type_, "__module__", None)
    if module not in (None, "typing", "typing_extensions", "builtins"):
        name = module + "." + name

    return name


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
    'Any'

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
