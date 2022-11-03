"""Manage the _console handler_."""

from __future__ import annotations
import logging
from typing import Optional
from collections.abc import Mapping

from splatlog.lib.text import fmt
from splatlog.lib.typeguard import satisfies
from splatlog.levels import is_level
from splatlog.locking import lock
from splatlog.rich_handler import RichHandler
from splatlog.typings import ConsoleHandlerCastable, RichConsoleCastable

_console_handler: Optional[logging.Handler] = None

__all__ = [
    "cast_console_handler",
    "get_console_handler",
    "set_console_handler",
]


def cast_console_handler(
    value: ConsoleHandlerCastable,
) -> Optional[logging.Handler]:
    """Convert a value into either a `logging.Handler` or `None`.

    If neither of those make sense raises a `TypeError`.

    ##### Examples #####

    1.  `True` is cast to a new `RichHandler` with all default attributes.

        ```python
        >>> cast_console_handler(True)
        <RichHandler (NOTSET)>

        ```

    2.  `False` and `None` cast to `None`.

        ```python
        >>> cast_console_handler(False) is None
        True

        >>> cast_console_handler(None) is None
        True

        ```

    3.  Any `logging.Handler` instance is simply returned.

        ```python
        >>> import sys

        >>> handler = logging.StreamHandler(sys.stdout)

        >>> cast_console_handler(handler) is handler
        True

        ```

    4.  Any `collections.abc.Mapping` is used as the keyword arguments to
        construct a new `RichHandler`.

        ```python
        >>> handler = cast_console_handler(
        ...     dict(
        ...         console=sys.stdout,
        ...         verbosity_levels=dict(
        ...             some_mod=((0, "WARNING"), (1, "INFO")),
        ...         )
        ...     )
        ... )

        >>> isinstance(handler, RichHandler)
        True

        >>> handler.console.file is sys.stdout
        True

        >>> handler.verbosity_levels
        {'some_mod': <VerbosityLevelResolver [0]: WARNING, [1, ...]: INFO>}

        ```

    5.  Anything that `RichHandler` can cast to a `rich.console.Console` (see
        `RichHandler.cast_console`) is assigned as the console in a new
        `RichHandler` instance.

        ```python
        >>> from io import StringIO

        >>> sio = StringIO()
        >>> handler = cast_console_handler(sio)

        >>> isinstance(handler, RichHandler)
        True

        >>> handler.console.file is sio
        True

        >>> import sys
        >>> cast_console_handler("stdout").console.file is sys.stdout
        True

        ```

    6.  Any log level name or value is assigned as the level to a new
        `RichHandler` instance.

        ```python
        >>> cast_console_handler(logging.DEBUG).level == logging.DEBUG
        True

        >>> cast_console_handler("DEBUG").level == logging.DEBUG
        True

        ```

        Note that in the extremely bizare case where you name a log level
        `"stdout"` (or `"STDOUT"`) you can not use `"stdout"` to create a
        handler with that level because `"stdout"` will be cast to a
        `RichHandler` with the `RichHandler.console` writing to `sys.stdout`.

        ```python
        >>> stdout_level_value = hash("stdout") # Use somewhat unique int

        >>> logging.addLevelName(stdout_level_value, "stdout")

        >>> cast_console_handler("stdout").level == stdout_level_value
        False

        ```

        Same applies for `"stderr"`.

    7.  Anythings else raises a `TypeError`.

        ```python
        >>> cast_console_handler([1, 2, 3])
        Traceback (most recent call last):
            ...
        TypeError:
            Expected
                None
                | logging.Handler
                | collections.abc.Mapping
                | bool
                | rich.console.Console
                | 'stdout'
                | 'stderr'
                | typing.IO[str]
                | int
                | str,
            given list: [1, 2, 3]

        ```
    """

    if value is True:
        return RichHandler()

    if value is None or value is False:
        return None

    if isinstance(value, logging.Handler):
        return value

    if isinstance(value, Mapping):
        return RichHandler(**value)

    if satisfies(value, RichConsoleCastable):
        return RichHandler(console=value)

    if is_level(value):
        return RichHandler(level=value)

    raise TypeError(
        "Expected {}, given {}: {}".format(
            fmt(ConsoleHandlerCastable),
            fmt(type(value)),
            fmt(value),
        )
    )


def get_console_handler() -> Optional[logging.Handler]:
    """Get the current console handler, if any."""

    return _console_handler


def set_console_handler(console: ConsoleHandlerCastable) -> None:
    """Set the current console handler.

    `console` is passed through `cast_console_handler` and added to the
    root logger. A reference is also stored in a private module variable.

    If there already was a console handler set it is removed from the root
    logger first.

    You can pass `None` or `False` to remove any console handler previously set.
    """

    global _console_handler

    handler = cast_console_handler(console)

    with lock():
        if handler is not _console_handler:
            root_logger = logging.getLogger()

            if _console_handler is not None:
                root_logger.removeHandler(_console_handler)

            if handler is not None:
                root_logger.addHandler(handler)

            _console_handler = handler
