from __future__ import annotations
import logging
import sys
from typing import Mapping, Optional, Sequence, Union

from splatlog.locking import lock
from splatlog.typings import LevelValue, Verbosity, asVerbosity
from splatlog.verbosity.verbosity_level_resolver import (
    VerbosityLevel,
    VerbosityLevelResolver,
)

VerbosityLevels = Mapping[str, VerbosityLevelResolver]
VerbosityLevelsCastable = Mapping[
    str, Union[VerbosityLevels, Sequence[VerbosityLevel]]
]

# Global State
# ============================================================================

_verbosity: Optional[Verbosity] = None
_verbosityLevels: VerbosityLevels = {}


def castVerbosityLevels(
    verbosityLevels: VerbosityLevelsCastable,
) -> VerbosityLevels:
    return {
        name: VerbosityLevelResolver.cast(levels)
        for name, levels in verbosityLevels.items()
    }


def getVerbosityLevels() -> VerbosityLevels:
    """Get the current logger name / verbosity levels mapping.

    > 📝 NOTE
    >
    > The returned `collections.abc.Mapping` is a copy of the one held in
    > internal global state. Adding or removing items will have no effect that
    > state.
    >
    > The copy is _shallow_ — it references the actual `VerbosityLevelConfig`
    > instances that are in use — but those are publically immutable. If you go
    > modifying private attributes your on your own as far as `splatlog` is
    > concerned.
    """
    return {**_verbosityLevels}


def setVerbosityLevels(verbosityLevels: VerbosityLevelsCastable) -> None:
    """

    > 📝 NOTE
    >
    > There is not way to add or remove individual name / levels mappings. This
    > is intentional as it avoids updating the internal global state and any
    > thread-safe logic that may come with that; the entire `dict` is written
    > as a single, unconditional set operation, which we understand to be
    > thread-safe from Python's point of vue (via the GIL).
    >
    > If you need to modify the levels, do your own get-modify-set sequence and
    > lock around it as needed for your application.

    ##### Examples #####

    ```python
    >>> setVerbosityLevels({
    ...     "splatlog": (
    ...         (0, "WARNING"),
    ...         (3, "INFO"),
    ...         (4, "DEBUG"),
    ...     ),
    ...     "my.app": (
    ...         (0, "INFO"),
    ...         (1, "DEBUG"),
    ...     )
    ... })

    ```
    """
    global _verbosityLevels
    _verbosityLevels = castVerbosityLevels(verbosityLevels)


def delVerbosityLevels(*, unsetLoggerLevels: bool = False) -> None:
    global _verbosityLevels
    if unsetLoggerLevels:
        with lock():
            for name, _ranges in _verbosityLevels.items():
                logging.getLogger(name).setLevel(logging.NOTSET)
    _verbosityLevels = {}


def getVerbosity() -> Optional[Verbosity]:
    return _verbosity


def setVerbosity(verbosity: Verbosity) -> None:
    global _verbosity
    verbosity = asVerbosity(verbosity)
    with lock():
        _verbosity = verbosity
        for name, ranges in _verbosityLevels.items():
            level = ranges.getLevel(verbosity)
            if level is not None:
                logging.getLogger(name).setLevel(level)


def delVerbosity(*, unsetLoggerLevels: bool = False) -> None:
    global _verbosity
    with lock():
        _verbosity = None
        if unsetLoggerLevels:
            for name, ranges in _verbosityLevels.items():
                logging.getLogger(name).setLevel(logging.NOTSET)
