"""Root of the `splatlog` package.

Imports pretty much everything else, so you should only really need to import
this.
"""

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

from splatlog.json.json_formatter import JSONFormatter


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
