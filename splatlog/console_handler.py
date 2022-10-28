from __future__ import annotations
import logging
import sys
from typing import IO, Optional, Union
from collections.abc import Mapping

from rich.console import Console
from splatlog.lib.text import fmt

from splatlog.lib.typeguard import satisfies
from splatlog.locking import lock
from splatlog.rich_handler import RichHandler
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

    if value is sys.stdout:
        return RichHandler(
            level_map={
                logging.CRITICAL: "out",
                logging.ERROR: "out",
                logging.WARNING: "out",
                logging.INFO: "out",
                logging.DEBUG: "out",
            }
        )

    if value is sys.stderr:
        return RichHandler(
            level_map={
                logging.CRITICAL: "err",
                logging.ERROR: "err",
                logging.WARNING: "err",
                logging.INFO: "err",
                logging.DEBUG: "err",
            }
        )

    if satisfies(value, IO):
        # TODO  This should be cleaner and easier; I'm thinking that instead of
        #       the level mapping you pass an object or function that does the
        #       mapping. This would support custom levels too.
        #
        return RichHandler(
            consoles={
                "custom": Console(file=value, theme=RichHandler.DEFAULT_THEME)
            },
            level_map={
                logging.CRITICAL: "custom",
                logging.ERROR: "custom",
                logging.WARNING: "custom",
                logging.INFO: "custom",
                logging.DEBUG: "custom",
            },
        )

    raise TypeError(
        "Expected {}, given {}: {!r}".format(
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
