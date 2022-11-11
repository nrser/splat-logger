"""Defines `SplatLogger` class."""

from __future__ import annotations
import logging
from functools import cache, wraps
from collections.abc import Generator

from splatlog.levels import get_level_value
from splatlog.lib.collections import partition_mapping
from splatlog.typings import Level, LevelValue


@cache
def get_logger(name: str) -> SplatLogger:
    return SplatLogger(logging.getLogger(name))


getLogger = get_logger


class SplatLogger(logging.LoggerAdapter):
    """\
    A `logging.Logger` extension that overrides the `logging.Logger._log` method
    the underlies all "log methods" (`logging.Logger.debug`,
    `logging.Logger.info`, etc) to treat the double-splat keyword arguments
    as a map of names to values to be logged.

    This map is added as `"data"` to the `extra` mapping that is part of the
    log method API, where it eventually is assigned as a `data` attribute
    on the emitted `logging.LogRecord`.

    This allows logging invocations like:

        logger.debug(
            "Check this out!",
            x="hey,
            y="ho",
            z={"lets": "go"},
        )

    which I (obviously) like much better.
    """

    def process(self, msg, kwargs):
        new_kwargs, data = partition_mapping(
            kwargs, {"exc_info", "extra", "stack_info", "stacklevel"}
        )
        if "extra" in new_kwargs:
            new_kwargs["extra"]["data"] = data
        else:
            new_kwargs["extra"] = {"data": data}
        return msg, new_kwargs

    def iter_handlers(self) -> Generator[logging.Handler, None, None]:
        logger = self.logger
        while logger:
            yield from logger.handlers
            if not logger.propagate:
                break
            else:
                logger = logger.parent

    def addHandler(self, hdlr: logging.Handler) -> None:
        """
        Delegate to the underlying logger.
        """
        return self.logger.addHandler(hdlr)

    def removeHandler(self, hdlr: logging.Handler) -> None:
        """
        Delegate to the underlying logger.
        """
        return self.logger.removeHandler(hdlr)

    @property
    def level(self) -> LevelValue:
        return self.logger.level

    def setLevel(self, level: Level) -> None:
        super().setLevel(get_level_value(level))

    def getChild(self, suffix):
        if self.logger.root is not self.logger:
            suffix = ".".join((self.logger.name, suffix))
        return getLogger(suffix)

    def inject(self, fn):
        @wraps(fn)
        def log_inject_wrapper(*args, **kwds):
            if "log" in kwds:
                return fn(*args, **kwds)
            else:
                return fn(*args, log=self.getChild(fn.__name__), **kwds)

        return log_inject_wrapper
