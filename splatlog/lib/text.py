from typing import Any, Optional

BUILTINS_MODULE = object.__module__


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
