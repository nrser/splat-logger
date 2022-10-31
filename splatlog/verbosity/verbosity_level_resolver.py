from __future__ import annotations
from itertools import pairwise
import sys
from typing import Optional
from collections.abc import Sequence

from splatlog.typings import Level, LevelValue, Verbosity, asVerbosity
from splatlog.levels import NOTSET, getLevelValue

VerbosityLevel = tuple[Verbosity, Level]
VerbosityRange = tuple[range, LevelValue]


class VerbosityLevelResolver:
    @staticmethod
    def computeVerbosityRanges(
        verbosityLevels: Sequence[VerbosityLevel],
    ) -> tuple[VerbosityRange, ...]:
        # Translate any `str` level names to their `int`` level value and check the
        # verbosity is in-bounds
        levels = [
            (asVerbosity(v), getLevelValue(l)) for v, l in verbosityLevels
        ]

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

    @classmethod
    def cast(cls, *args, **kwds) -> VerbosityLevelResolver:
        if len(args) == 1 and len(kwds) == 0 and isinstance(args[0], cls):
            return args[0]
        return cls(*args, **kwds)

    _levels: tuple[VerbosityLevel, ...]
    _ranges: tuple[VerbosityRange, ...]

    def __init__(self, levels: Sequence[tuple[Verbosity, Level]]):
        self._levels = tuple(
            (verbosity, getLevelValue(level)) for verbosity, level in levels
        )
        self._ranges = VerbosityLevelResolver.computeVerbosityRanges(levels)

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
