from __future__ import annotations
import logging
from typing import Optional

from splatlog.typings import *
from splatlog.levels import *
from splatlog.names import *
from splatlog.verbosity import *
from splatlog.locking import *
from splatlog.splat_logger import *
from splatlog.rich_handler import *
from splatlog.json import *
from splatlog.named_handlers import *


def setup(
    *,
    level: Optional[Level] = None,
    verbosity_levels: Optional[VerbosityLevelsCastable] = None,
    verbosity: Optional[Verbosity] = None,
    console: ConsoleHandlerCastable = None,
    file: FileHandlerCastable = None,
) -> None:
    if level is not None:
        logging.getLogger().setLevel(get_level_value(level))

    if verbosity_levels is not None:
        set_verbosity_levels(verbosity_levels)

    if verbosity is not None:
        set_verbosity(verbosity)

    if console is not None:
        set_named_handler("console", console)

    if file is not None:
        set_named_handler("file", file)
