# TODO  This file is _not_ called `setup.py` because

from __future__ import annotations
import logging
from typing import Optional


from splatlog.typings import (
    ConsoleHandlerCastable,
    ExportHandlerCastable,
    Level,
    Verbosity,
    VerbosityLevelsCastable,
)
from splatlog.levels import get_level_value
from splatlog.verbosity import set_verbosity_levels, set_verbosity
from splatlog.named_handlers import set_named_handler


def setup(
    *,
    level: Optional[Level] = None,
    verbosity_levels: Optional[VerbosityLevelsCastable] = None,
    verbosity: Optional[Verbosity] = None,
    console: ConsoleHandlerCastable = None,
    export: ExportHandlerCastable = None,
    **custom_named_handlers,
) -> None:
    """Set things up!"""

    if level is not None:
        logging.getLogger().setLevel(get_level_value(level))

    if verbosity_levels is not None:
        set_verbosity_levels(verbosity_levels)

    if verbosity is not None:
        set_verbosity(verbosity)

    if console is not None:
        set_named_handler("console", console)

    if export is not None:
        set_named_handler("export", export)

    for name, value in custom_named_handlers.items():
        if value is not None:
            set_named_handler(name, value)
