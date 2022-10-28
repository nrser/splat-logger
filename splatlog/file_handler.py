from __future__ import annotations
import logging
from pathlib import Path
import sys
from typing import IO, Optional, Union
from collections.abc import Mapping

from rich.console import Console
from splatlog.json.json_encoder import JSONEncoder
from splatlog.json.json_formatter import JSONFormatter
from splatlog.lib.text import fmt

from splatlog.lib.typeguard import satisfies
from splatlog.locking import lock
from splatlog.rich_handler import RichHandler
from splatlog.typings import HandlerCastable, Level

FileHandlerCastable = Union[HandlerCastable, str, Path]

_fileHandler: Optional[logging.Handler] = None


def castFileHandler(value) -> Optional[logging.Handler]:
    if value is None:
        return None

    if isinstance(value, logging.Handler):
        return value

    if isinstance(value, Mapping):
        handler = logging.FileHandler(
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
        handler = logging.FileHandler(filename=value)
        handler.formatter = JSONFormatter()
        return handler

    raise TypeError(
        "Expected {}, given {}: {!r}".format(
            fmt(Union[None, logging.Handler, Mapping, str, Path]),
            fmt(type(value)),
            fmt(value),
        )
    )


def getFileHandler() -> Optional[logging.Handler]:
    return _fileHandler


def setFileHandler(file: FileHandlerCastable) -> None:
    global _fileHandler

    handler = castFileHandler(file)

    with lock():
        if handler is not _fileHandler:
            rootLogger = logging.getLogger()

            if _fileHandler is not None:
                rootLogger.removeHandler(_fileHandler)

            if handler is not None:
                rootLogger.addHandler(handler)

            _fileHandler = handler
