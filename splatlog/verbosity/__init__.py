from __future__ import annotations
import logging
import sys
from itertools import pairwise
from typing import Mapping, Optional, Sequence, TypeGuard, Union

from splatlog.levels import NOTSET, getLevelValue
from splatlog.lib.text import fmt
from splatlog.locking import lock
from splatlog.typings import Level, LevelValue, Verbosity

VerbosityLevel = tuple[Verbosity, Level]
VerbosityLevelsMap = dict[
    str, Sequence[Union[VerbosityLevel, "VerbosityRanges"]]
]
VerbosityRange = tuple[range, LevelValue]

# Global State
# ============================================================================

_verbosity: Optional[Verbosity] = None
_verbosityLevels: dict[str, VerbosityRanges] = {}


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


def computeVerbosityRanges(
    verbosityLevels: Sequence[VerbosityLevel],
) -> tuple[VerbosityRange, ...]:
    # Translate any `str` level names to their `int`` level value and check the
    # verbosity is in-bounds
    levels = [(asVerbosity(v), getLevelValue(l)) for v, l in verbosityLevels]

    # Add the "upper cap" with a max verbosity of `sys.maxsize`. The level value
    # doesn't matter, so we use `NOTSET`
    levels.append((sys.maxsize, NOTSET))

    # Sort those by the verbosity (first member of the tuple)
    levels.sort(key=lambda vl: vl[0])

    # The result ranges between sort-adjacent verbosities mapped to the level
    # value of the first verbosity/level pair
    return tuple(
        (range(v_1, v_2), l_1) for (v_1, l_1), (v_2, _) in pairwise(levels)
    )


class VerbosityRanges:
    @classmethod
    def cast(cls, *args, **kwds) -> VerbosityRanges:
        if len(args) == 1 and len(kwds) == 0 and isinstance(args[0], cls):
            return args[0]
        return cls(*args, **kwds)

    _levels: tuple[VerbosityLevel, ...]
    _ranges: tuple[VerbosityRange, ...]

    def __init__(self, levels: Sequence[tuple[Verbosity, Level]]):
        self._levels = tuple(
            (verbosity, getLevelValue(level)) for verbosity, level in levels
        )
        self._ranges = computeVerbosityRanges(levels)

    @property
    def levels(self) -> tuple[VerbosityLevel, ...]:
        """The verbosity/level mappings used to compute
        `VerbosityRanges.ranges`, as they were passed in at construction.
        """
        return self._levels

    @property
    def ranges(self) -> tuple[VerbosityRange, ...]:
        """The range/level mappings computed from `VerbosityRanges.levels."""
        return self._ranges

    def getLevel(self, verbosity: Verbosity) -> Optional[LevelValue]:
        """Get the log level (`int` value) for a verbosity, or `None` if there
        is not one.
        """
        for rng, levelValue in self._ranges:
            if verbosity in rng:
                return levelValue
        return None


def getVerbosityLevels() -> Mapping[str, VerbosityRanges]:
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


def setVerbosityLevels(levelsMap: VerbosityLevelsMap) -> None:
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
        "splatlog": (
            (0, WARNING),
            (3, INFO),
            (4, DEBUG),
        ),
        "my.app": (
            (0, INFO),
            (1, DEBUG),
        )
    })

    ```
    """
    global _verbosityLevels
    _verbosityLevels = {
        name: VerbosityRanges.cast(levels) for name, levels in levelsMap.items()
    }


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
