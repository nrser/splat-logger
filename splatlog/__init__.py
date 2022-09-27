from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Union
from collections.abc import Iterable, Mapping

from splatlog.roles import APP_ROLE, LIB_ROLE, SERVICE_ROLE

from .typings import *
from .levels import *
from .splat_manager import SplatManager
from .splat_logger import SplatLogger
from .rich_handler import RichHandler
from .json.json_formatter import JSONFormatter
from .json.json_encoder import JSONEncoder

# TODO  Not longer needed, as `get_logger` returns `SplatLogger` that type can
#       be used directly, and `logging.Logger` can be used in general.
TLogger = logging.Logger


def root_name(module_name: str) -> str:
    return module_name.split(".")[0]


def _announce_debug(logger):
    logger.debug(
        "[logging.level.debug]DEBUG[/] logging "
        + f"[bold green]ENABLED[/] for [blue]{logger.name}.*[/]"
    )


def _ensure_logger_class() -> None:
    logger_class = logging.getLoggerClass()
    if not (
        logger_class is SplatLogger or issubclass(logger_class, SplatLogger)
    ):
        logging.setLoggerClass(SplatLogger)


# NOTE  Just override the logging class in init. This makes things _much_
#       simpler. We're going to do it anyways in any situation I can currently
#       conceive of.
#
#       The downside to this is simply having (global) side-effect from import,
#       but hopefully this is a case where that is worth it.
#
_ensure_logger_class()

DEFAULT_MANAGER = SplatManager(
    builtin_roles=(APP_ROLE, SERVICE_ROLE, LIB_ROLE),
)

getLogger = DEFAULT_MANAGER.getLogger
setup = DEFAULT_MANAGER.setup
getVerbosity = DEFAULT_MANAGER.getVerbosity
setVerbosity = DEFAULT_MANAGER.setVerbosity
delVerbosity = DEFAULT_MANAGER.delVerbosity

roles = DEFAULT_MANAGER.roles
hasRole = DEFAULT_MANAGER.hasRole
getRole = DEFAULT_MANAGER.getRole
createRole = DEFAULT_MANAGER.createRole
deleteRole = DEFAULT_MANAGER.deleteRole

getRoleLevel = DEFAULT_MANAGER.getRoleLevel
assignRole = DEFAULT_MANAGER.assignRole
clearRole = DEFAULT_MANAGER.clearRole
addHandler = DEFAULT_MANAGER.addHandler
removeHandler = DEFAULT_MANAGER.removeHandler

if __name__ == "__main__":
    import doctest

    doctest.testmod()
