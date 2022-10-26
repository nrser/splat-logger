from __future__ import annotations
from contextlib import nullcontext
import logging
from pathlib import Path
from typing import IO, Optional, Union
from collections.abc import Mapping

from rich.console import Console

from .lib.typeguard import satisfies
from .typings import *
from .levels import *
from .verbosity import *
from .handler import *
from .splat_adapter import SplatAdapter, getLogger
from .rich_handler import RichHandler
from .json.json_formatter import JSONFormatter
from .json.json_encoder import JSONEncoder


HandlerCastable = Union[None, logging.Handler, Mapping]
ConsoleHandlerCastable = Union[HandlerCastable, bool, Level, IO]
FileHandlerCastable = Union[HandlerCastable, str, Path]

_NULL_CONTEXT = nullcontext()

_consoleHandler: Optional[logging.Handler] = None
_fileHandler: Optional[logging.Handler] = None


def rootName(module_name: str) -> str:
    return module_name.split(".")[0]


# def _announce_debug(logger):
#     logger.debug(
#         "[logging.level.debug]DEBUG[/] logging "
#         + f"[bold green]ENABLED[/] for [blue]{logger.name}.*[/]"
#     )


def setup(
    *,
    level: Optional[Level] = None,
    verbosityLevels: Optional[VerbosityLevelsMap] = None,
    verbosity: Optional[Verbosity] = None,
    console: ConsoleHandlerCastable = True,
    file: FileHandlerCastable = None,
) -> Optional[SplatAdapter]:
    if level is not None:
        logging.getLogger().setLevel(getLevelValue(level))

    if verbosityLevels is not None:
        setVerbosityLevels(verbosityLevels)

    if verbosity is not None:
        setVerbosity(verbosity)

    if console is not None:
        setConsoleHandler(console)

    if file is not None:
        setFileHandler(file)


def sync():
    lock = getattr(logging, "_lock", None)
    if lock:
        return lock
    return _NULL_CONTEXT


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
                CRITICAL: "out",
                ERROR: "out",
                WARNING: "out",
                INFO: "out",
                DEBUG: "out",
            }
        )

    if value is sys.stderr:
        return RichHandler(
            level_map={
                CRITICAL: "err",
                ERROR: "err",
                WARNING: "err",
                INFO: "err",
                DEBUG: "err",
            }
        )

    if satisfies(value, IO):
        return RichHandler(
            consoles={
                "custom": Console(file=value, theme=RichHandler.DEFAULT_THEME)
            },
            level_map={
                CRITICAL: "custom",
                ERROR: "custom",
                WARNING: "custom",
                INFO: "custom",
                DEBUG: "custom",
            },
        )

    raise TypeError(
        "Expected {}, given {}: {!r}".format(
            fmt(Union[None, Handler, Mapping, Level]),
            fmt(type(value)),
            fmt(value),
        )
    )


def getConsoleHandler() -> Optional[logging.Handler]:
    return _consoleHandler


def setConsoleHandler(console: ConsoleHandlerCastable) -> None:
    global _consoleHandler

    handler = castConsoleHandler(console)

    with sync():
        if handler is not _consoleHandler:
            rootLogger = logging.getLogger()

            if _consoleHandler is not None:
                rootLogger.removeHandler(_consoleHandler)

            if handler is not None:
                rootLogger.addHandler(handler)

            _consoleHandler = handler


def castFileHandler(value) -> Optional[logging.Handler]:
    if value is None:
        return None

    if isinstance(value, Handler):
        return value

    if isinstance(value, Mapping):
        handler = PriorityFileHandler(
            **{k: v for k, v in value.items() if k != "formatter"}
        )

        if "formatter" in value:
            formatter_kwds = {
                k: v for k, v in value["formatter"].items() if k != "encoder"
            }

            if "encoder" in value["formatter"]:
                formatter_kwds["encoder"] = JSONEncoder(
                    **value["formatter"]["encoder"]
                )

            handler.formatter = JSONFormatter(**formatter_kwds)

        else:
            handler.formatter = JSONFormatter()

        return handler

    if isinstance(value, (str, Path)):
        handler = PriorityFileHandler(filename=value)
        handler.formatter = JSONFormatter()
        return handler

    raise TypeError(
        "Expected {}, given {}: {!r}".format(
            fmt(Union[None, Handler, Mapping, str, Path]),
            fmt(type(value)),
            fmt(value),
        )
    )


def getFileHandler() -> Optional[logging.Handler]:
    return _fileHandler


def setFileHandler(file: FileHandlerCastable) -> None:
    global _fileHandler

    handler = castFileHandler(file)

    with sync():
        if handler is not _fileHandler:
            rootLogger = logging.getLogger()

            if _fileHandler is not None:
                rootLogger.removeHandler(_fileHandler)

            if handler is not None:
                rootLogger.addHandler(handler)

            _fileHandler = handler
