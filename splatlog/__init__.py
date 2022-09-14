from __future__ import annotations
import logging
from typing import Iterable, Optional, Union

from .typings import *
from .levels import *
from .lib import each
from .splat_logger import SplatLogger
from .log_getter import LogGetter
from .rich_handler import RichHandler
from .json.json_formatter import JSONFormatter
from .json.json_encoder import JSONEncoder

# Union type representing when we don't know (or care) if we're getting a
# LogGetter proxy or an actual Logger
TLogger = Union[logging.Logger, LogGetter]


def root_name(module_name: str) -> str:
    return module_name.split(".")[0]


def _announce_debug(logger):
    logger.debug(
        "[logging.level.debug]DEBUG[/] logging "
        + f"[bold green]ENABLED[/] for [blue]{logger.name}.*[/]"
    )


def get_logger(*name: str) -> LogGetter:
    """\
    Returns a proxy to a logger where construction is deferred until first use.

    See `splatlog.log_getter.LogGetter`.
    """
    return LogGetter(*name)


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
    module_names: Union[str, Iterable[str]],
    level: Optional[TLevelSetting] = None,
    *,
    module_type: ModuleType = ModuleType.APP,
) -> None:
    _ensure_logger_class()

    if level is None:
        level_i = (
            DEFAULT_LIB_LEVEL
            if module_type == ModuleType.LIB
            else DEFAULT_APP_LEVEL
        )
    else:
        level_i = level_for(level)

    for module_name in each(module_names, str):
        logger = logging.getLogger(module_name)

        if not isinstance(logger, SplatLogger):
            raise TypeError(
                f"Can not setup -- logger for {module_name!r} is not a "
                + f"SplatLogger instance, it's a {type(logger)!r}"
            )

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

        if logger.console_handler is None:
            logger.console_handler = RichHandler(level=level_i)
        else:
            logger.console_handler.setLevel(level_i)


# Support the weird camel-case that stdlib `logging` uses...
getLogger = get_logger
setLevel = set_level


if __name__ == "__main__":
    import doctest

    doctest.testmod()
