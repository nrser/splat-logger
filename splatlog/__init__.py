from __future__ import annotations
import logging
from typing import Optional, Union

from .typings import *
from .levels import *
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


def get_logger(*name: str) -> SplatLogger:
    """Gets a logger, like `logging.getLogger`."""

    name = ".".join(name)
    logger = logging.getLogger(name)
    if not isinstance(logger, SplatLogger):
        raise TypeError(f"Expected SplatLogger, got {type(logger)}: {logger!r}")
    return logger


def set_level(module_name: str, level: TLevelSetting) -> None:
    level_i = level_for(level)
    logger = get_logger(module_name)
    prev_level = logger.level
    logger.console_handler.setLevel(level_i)
    if level_i == DEBUG and level_i != prev_level:
        _announce_debug(logger)


def _ensure_logger_class() -> None:
    logger_class = logging.getLoggerClass()
    if not (
        logger_class is SplatLogger or issubclass(logger_class, SplatLogger)
    ):
        logging.setLoggerClass(SplatLogger)


def setup(
    module_name: str,
    level: Optional[TLevelSetting] = None,
    *,
    module_role: ModuleType = ModuleType.APP,
    console: Union[bool, TLevelSetting, logging.Handler] = True,
    propagate: bool = True,
) -> SplatLogger:
    """
    #### Parameters ####

    -   `console` — Supports a few different behaviors depending on the value:
        1.  `True` (default) — create a `RichHandler` instance to
            populate `SplatLogger.console_handler` (unless it is
            already populated).
        2.  `False` — Don't do anything involving
            `SplatLogger.console_handler`.
        3.  `TLevelSetting` — Set the `SplatLogger.console_handler`
            level, creating a `RichHandler` and assigning it if needed.
        4.  `logging.Handler` — Assign this handler to
            `SplatLogger.console_handler`. Assumes you've already set the
            handler's level how you like, and does not touch it regardless of
            the `level` argument.

    """

    level_value = resolve_level_value(level, module_role)

    logger = get_logger(module_name)
    logger.propagate = propagate
    logger.module_role = module_role

    # To facilitate independent log levels for different handlers — say a
    # JSON handler that writes all levels to the log, regardless of what
    # the console handler is set to — we control the log level on the
    # handlers themselves, not on the loggers.
    #
    # However, the level of the top-most splat logger must be set to
    # something higher than logging.NOTSET (the default), because
    # `logging.NOTSET` will cause records to climb further up to the chain,
    # usually to `logging.root`, which has a default level of
    # `logging.WARNING`.
    #
    logger.setLevel(logging.NOTSET + 1)

    if console is False:
        pass
    elif console is True:
        with logger.exclusive_console_handler() as console_handler:
            if console_handler is None:
                logger.console_handler = RichHandler(level=level_value)
            else:
                console_handler.setLevel(level_value)
    elif isinstance(console, logging.Handler):
        logger.console_handler = console
    else:
        console_level = level_for(console)
        with logger.exclusive_console_handler() as console_handler:
            if console_handler is None:
                logger.console_handler = RichHandler(level=console_level)
            else:
                console_handler.setLevel(console_level)

    return logger


# Support the weird camel-case that stdlib `logging` uses...
getLogger = get_logger
setLevel = set_level

# NOTE  Just override the logging class in init. This makes things _much_
#       simpler. We're going to do it anyways in any situation I can currently
#       conceive of.
#
#       The downside to this is simply having (global) side-effect from import,
#       but hopefully this is a case where that is worth it.
#
_ensure_logger_class()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
