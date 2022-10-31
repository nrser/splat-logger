from __future__ import annotations
import logging
import sys
from types import TracebackType
from typing import Any, Literal, Optional, Type, TypeGuard, Union, Mapping

from splatlog.lib.text import fmt

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

# Verbosity
# ============================================================================
#
# Representation of a common "verbose" flag, where the repetition is stored as
# a count:
#
# (no flag) -> 0
# -v        -> 1
# -vv       -> 2
# -vvv      -> 3
#
Verbosity = int


def isVerbosity(x: object) -> TypeGuard[Verbosity]:
    return isinstance(x, int) and x >= 0 and x < sys.maxsize


def asVerbosity(x: object) -> Verbosity:
    if isVerbosity(x):
        return x
    raise TypeError(
        (
            "Expected verbosity to be non-negative integer less than "
            "`sys.maxsize`, given {}: {}"
        ).format(fmt(type(x)), fmt(x))
    )


# Etc
# ============================================================================

# Modes that makes sense to open a logging file in
FileHandlerMode = Literal["a", "ab", "w", "wb"]

# It's not totally clear to me what the correct typing of "exc info" is... I
# read the CPython source, I looked at the Pylance types (from Microsoft), and
# this is what I settled on for this use case.
ExcInfo = tuple[Type[BaseException], BaseException, Optional[TracebackType]]

HandlerCastable = Union[None, logging.Handler, Mapping]
