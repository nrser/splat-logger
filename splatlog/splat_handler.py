import logging
from typing import Optional

from splatlog.typings import Level
from splatlog.levels import getLevelValue
from splatlog.verbosity import VerbosityLevelsMap, VerbosityRanges
from splatlog.verbosity.verbosity_levels_filter import VerbosityLevelsFilter


class SplatHandler(logging.Handler):
    """ """

    def __init__(
        self,
        level: Level = logging.NOTSET,
        *,
        verbosityLevels: Optional[VerbosityLevelsMap] = None,
    ):
        super().__init__(getLevelValue(level))
        VerbosityLevelsFilter.setOn(self, verbosityLevels)

    def getVerbosityLevels(self) -> Optional[dict[str, VerbosityRanges]]:
        if filter := VerbosityLevelsFilter.getFrom(self):
            return filter.verbosityLevels

    def setVerbosityLevels(
        self, verbosityLevels: Optional[VerbosityLevelsMap]
    ) -> None:
        VerbosityLevelsFilter.setOn(self, verbosityLevels)

    def delVerbosityLevels(self) -> None:
        VerbosityLevelsFilter.removeFrom(self)

    verbosityLevels = property(
        getVerbosityLevels,
        setVerbosityLevels,
        delVerbosityLevels,
    )
