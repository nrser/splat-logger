import logging
from typing import Optional

from splatlog.typings import Level
from splatlog.levels import getLevelValue
from splatlog.verbosity import (
    VerbosityLevelsCastable,
    VerbosityLevels,
)
from splatlog.verbosity.verbosity_levels_filter import VerbosityLevelsFilter


class SplatHandler(logging.Handler):
    """ """

    def __init__(
        self,
        level: Level = logging.NOTSET,
        *,
        verbosityLevels: Optional[VerbosityLevelsCastable] = None,
    ):
        super().__init__(getLevelValue(level))
        VerbosityLevelsFilter.setOn(self, verbosityLevels)

    def getVerbosityLevels(self) -> Optional[VerbosityLevels]:
        if filter := VerbosityLevelsFilter.getFrom(self):
            return filter.verbosityLevels

    def setVerbosityLevels(
        self, verbosityLevels: Optional[VerbosityLevelsCastable]
    ) -> None:
        VerbosityLevelsFilter.setOn(self, verbosityLevels)

    def delVerbosityLevels(self) -> None:
        VerbosityLevelsFilter.removeFrom(self)

    verbosityLevels = property(
        getVerbosityLevels,
        setVerbosityLevels,
        delVerbosityLevels,
    )
