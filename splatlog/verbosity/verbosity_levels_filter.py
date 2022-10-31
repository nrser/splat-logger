import logging
from typing import Optional

from splatlog.typings import Level
from splatlog.verbosity.verbosity_state import (
    VerbosityLevels,
    VerbosityLevelsCastable,
    castVerbosityLevels,
    getVerbosity,
)


def isNameOrAncestorName(loggerName: str, ancestorName: str):
    """
    ##### Examples #####

    ```python
    >>> isNameOrAncestorName("splatlog", "splatlog")
    True

    >>> isNameOrAncestorName("splatlog.lib", "splatlog")
    True

    >>> isNameOrAncestorName("splatlog", "blah")
    False

    >>> isNameOrAncestorName("splatlog", "splat")
    False

    >>> isNameOrAncestorName("splatlog", "splat")
    False

    ```
    """
    if not loggerName.startswith(ancestorName):
        return False
    ancestorNameLength = len(ancestorName)
    return (
        ancestorNameLength == len(loggerName)  # same as == at this point
        or loggerName[ancestorNameLength] == "."
    )


class VerbosityLevelsFilter(logging.Filter):
    @classmethod
    def getFrom(cls, filterer: logging.Filterer):
        for filter in filterer.filters:
            if isinstance(filter, cls):
                return filter

    @classmethod
    def setOn(
        cls,
        filterer: logging.Filterer,
        verbosityLevels: Optional[VerbosityLevelsCastable],
    ) -> None:
        cls.removeFrom(filterer)

        if verbosityLevels is None:
            return

        filter = cls(verbosityLevels)

        filterer.addFilter(filter)

    @classmethod
    def removeFrom(cls, filterer: logging.Filterer):
        for filter in [f for f in filterer.filters if isinstance(f, cls)]:
            filterer.removeFilter(filter)

    _verbosityLevels: VerbosityLevels

    def __init__(self, verbosityLevels: VerbosityLevelsCastable):
        super().__init__()
        self._verbosityLevels = castVerbosityLevels(verbosityLevels)

    @property
    def verbosityLevels(self) -> VerbosityLevels:
        return self._verbosityLevels

    def filter(self, record: logging.LogRecord) -> bool:
        if self._verbosityLevels is None:
            return True

        verbosity = getVerbosity()

        if verbosity is None:
            return True

        for name, ranges in self._verbosityLevels.items():
            if isNameOrAncestorName(record.name, name):
                effectiveLevel = ranges.getLevel(verbosity)
                return (
                    effectiveLevel is None or record.levelno >= effectiveLevel
                )

        return True
