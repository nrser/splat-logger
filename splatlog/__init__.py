from __future__ import annotations
import logging
from typing import Optional

from splatlog.typings import *
from splatlog.levels import *
from splatlog.verbosity import *
from splatlog.locking import *
from splatlog.splat_logger import *
from splatlog.rich_handler import *
from splatlog.json import *
from splatlog.console_handler import *
from splatlog.file_handler import *


def rootName(moduleName: str) -> str:
    return moduleName.split(".")[0]


def setup(
    *,
    level: Optional[Level] = None,
    verbosityLevels: Optional[VerbosityLevelsMap] = None,
    verbosity: Optional[Verbosity] = None,
    console: ConsoleHandlerCastable = True,
    file: FileHandlerCastable = None,
) -> Optional[SplatLogger]:
    if level is not None:
        logging.getLogger().setLevel(getLevelValue(level))

    if verbosityLevels is not None:
        setVerbosityLevels(verbosityLevels)

    if verbosity is not None:
        setVerbosity(verbosity)

    if console is not None:
        setConsoleHandler(console)

    if file is not None:
        setFileHandler(file)
