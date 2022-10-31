import logging
from typing import Optional
from splatlog.levels import getLevelValue

from splatlog.typings import Level
from splatlog.verbosity import VerbosityLevelsMap, VerbosityRanges, getVerbosity


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


class VerbosityLevelsHandler(logging.Handler):
    _verbosityLevels: Optional[dict[str, VerbosityRanges]] = None

    def __init__(
        self,
        level: Level = logging.NOTSET,
        *,
        verbosityLevels: Optional[VerbosityLevelsMap] = None,
    ):
        super().__init__(getLevelValue(level))
        if verbosityLevels is not None:
            self._verbosityLevels = {
                name: VerbosityRanges.cast(levels)
                for name, levels in verbosityLevels.items()
            }

    def filter(self, record: logging.LogRecord) -> bool:
        # NOTE  We skip calling up to `logging.Handler.filter` — which is
        #       actually `logging.Filter.filter` because Handler does not
        #       override it — because `logging.Handler` does not initialize
        #       `logging.Filter` with any `name`, so it will always return
        #       `True`.
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
