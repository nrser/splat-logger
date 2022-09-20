from __future__ import annotations
from inspect import isclass
from types import TracebackType
from typing import Any, Literal, Optional, Type, Union, get_args
from enum import Enum


ModuleRole = Literal["app", "lib"]


class ModuleType(Enum):
    APP = "app"
    LIB = "lib"


# The "actual" representation of a log level, per the built-in `logging`
# package. Log messages with an equal or higher level number than the
# logger class' level number are emitted; those with a lower log number are
# ignored.
TLevel = int

# Canonical names of the supported log levels.
TLevelName = Literal[
    "CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", "NOTSET"
]

# A more friendly / useful representation of a level, such as it's name (case
# insensitive). Admits level numbers as well, including as strings.
TLevelSetting = Union[TLevel, str]

# Representation of a common "verbose" flag, where the repetition is stored as
# a count:
#
# (no flag) -> None or 0
# -v        -> 1
# -vv       -> 2
# -vvv      -> 3
#
TVerbosity = Union[None, int]

TExcInfo = tuple[Type[BaseException], BaseException, Optional[TracebackType]]


def is_exc_info(exc_info: Any) -> bool:
    return (
        isinstance(exc_info, tuple)
        and len(exc_info) == 3
        and isclass(exc_info[0])
        and issubclass(exc_info[0], BaseException)
        and isinstance(exc_info[1], BaseException)
        and (exc_info[2] is None or isinstance(exc_info[2], TracebackType))
    )
