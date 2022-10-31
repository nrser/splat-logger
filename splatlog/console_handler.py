from __future__ import annotations
import logging
import sys
from typing import IO, Literal, Optional, Union
from collections.abc import Mapping

from rich.console import Console
from splatlog.lib.text import fmt

from splatlog.lib.typeguard import satisfies
from splatlog.locking import lock
from splatlog.rich_handler import ConsoleCastable, RichHandler
from splatlog.typings import HandlerCastable, Level


ConsoleHandlerCastable = Union[HandlerCastable, bool, Level, IO]

_consoleHandler: Optional[logging.Handler] = None


def castConsoleHandler(value) -> Optional[logging.Handler]:
    if value is True:
        return RichHandler.default()

    if value is None or value is False:
        return None

    if isinstance(value, logging.Handler):
        return value

    if isinstance(value, Mapping):
        return RichHandler(**value)

    if satisfies(value, Level):
        return RichHandler(level=value)

    if satisfies(value, ConsoleCastable):
        return RichHandler(console=value)

    raise TypeError(
        "Expected {}, given {}: {}".format(
            fmt(Union[None, logging.Handler, Mapping, Level]),
            fmt(type(value)),
            fmt(value),
        )
    )


def getConsoleHandler() -> Optional[logging.Handler]:
    return _consoleHandler


def setConsoleHandler(console: ConsoleHandlerCastable) -> None:
    global _consoleHandler

    handler = castConsoleHandler(console)

    with lock():
        if handler is not _consoleHandler:
            rootLogger = logging.getLogger()

            if _consoleHandler is not None:
                rootLogger.removeHandler(_consoleHandler)

            if handler is not None:
                rootLogger.addHandler(handler)

            _consoleHandler = handler
