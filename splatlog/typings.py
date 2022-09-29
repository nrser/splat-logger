from __future__ import annotations
from inspect import isclass
from types import TracebackType
from typing import Any, Literal, Optional, Type, Union
from enum import Enum


FileHandlerMode = Literal["a", "ab", "w", "wb"]

# Level Types
# ============================================================================
#
# There has always been some... frustration... typing `logging` levels. There is
# no typing in the builtin module. As such, this _kind-of_ follows the VSCode /
# PyLance typings from Microsoft. At least that way it corresponds decently to
# _something_ we're likely to be using.
#

# The "actual" representation of a log level, per the built-in `logging`
# package. Log messages with an equal or higher level number than the
# logger class' level number are emitted; those with a lower log number are
# ignored.
LevelValue = int

LevelName = str

# This corresponds to the `logging._Level` type in PyLance.
Level = Union[LevelValue, LevelName]

# Canonical names of the supported log levels.
BuiltinLevelName = Literal[
    "CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", "NOTSET"
]

# A more friendly / useful representation of a level, such as it's name (case
# insensitive). Admits level numbers as well, including as strings.
TLevelSetting = Level

# Representation of a common "verbose" flag, where the repetition is stored as
# a count:
#
# (no flag) -> 0
# -v        -> 1
# -vv       -> 2
# -vvv      -> 3
#
Verbosity = int

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
