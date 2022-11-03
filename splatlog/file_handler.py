from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Union
from collections.abc import Mapping

from splatlog.json.json_encoder import JSONEncoder
from splatlog.json.json_formatter import JSONFormatter
from splatlog.lib.text import fmt

from splatlog.locking import lock
from splatlog.typings import HandlerCastable, FileHandlerCastable
from splatlog.verbosity.verbosity_levels_filter import VerbosityLevelsFilter

_file_handler: Optional[logging.Handler] = None

__all__ = [
    "cast_file_handler",
    "get_file_handler",
    "set_file_handler",
]


def cast_file_handler(value) -> Optional[logging.Handler]:
    if value is None:
        return None

    if isinstance(value, logging.Handler):
        return value

    if isinstance(value, Mapping):
        handler = logging.FileHandler(
            **{
                k: v
                for k, v in value.items()
                if k != "formatter" and k != "verbosityLevels"
            }
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

        VerbosityLevelsFilter.set_on(handler, value.get("verbosityLevels"))

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


def get_file_handler() -> Optional[logging.Handler]:
    return _file_handler


def set_file_handler(file: FileHandlerCastable) -> None:
    global _file_handler

    handler = cast_file_handler(file)

    with lock():
        if handler is not _file_handler:
            rootLogger = logging.getLogger()

            if _file_handler is not None:
                rootLogger.removeHandler(_file_handler)

            if handler is not None:
                rootLogger.addHandler(handler)

            _file_handler = handler
