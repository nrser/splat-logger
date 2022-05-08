from __future__ import annotations
from typing import Literal, TypeVar, Union
from enum import Enum


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

#
TVerbosity = int
