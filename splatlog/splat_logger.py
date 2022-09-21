"""Defines `SplatLogger` class."""

from __future__ import annotations
import logging
from typing import (
    Any,
    Optional,
    Mapping,
)
from functools import wraps
from threading import RLock
from collections.abc import Generator

from splatlog.json.json_encoder import JSONEncoder
from splatlog.json.json_formatter import LOCAL_TIMEZONE, JSONFormatter
from splatlog.handler import PriorityHandler
from splatlog.rich_handler import RichHandler
from splatlog.typings import ModuleType
from splatlog.handler_descriptor import HandlerDescriptor


def build_console_handler(logger, level=logging.NOTSET):
    return RichHandler(level=level)


def build_json_handler(
    logger,
    level=logging.NOTSET,
    filename="/var/log/{name}.log.json",
    mode="a",
    encoding="utf-8",
    delay=False,
    errors=None,
    encoder=None,
    tz=LOCAL_TIMEZONE,
    use_Z_for_utc=True,
):
    handler = logging.FileHandler(
        filename=filename.format(name=logger.name),
        mode=mode,
        encoding=encoding,
        delay=delay,
        errors=errors,
    )

    if isinstance(encoder, Mapping):
        encoder = JSONEncoder(**encoder)

    handler.formatter = JSONFormatter(
        encoder=encoder,
        tz=tz,
        use_Z_for_utc=use_Z_for_utc,
    )

    handler.setLevel(level)

    return handler


class SplatLogger(logging.getLoggerClass()):
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

    console_handler = HandlerDescriptor(build=build_console_handler)
    json_handler = HandlerDescriptor(build=build_json_handler)

    # _console_handler: Optional[RichHandler] = None
    _handler_lock: RLock
    _is_root: bool = False
    _module_role: Optional[ModuleType] = None

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self._handler_lock = RLock()

    @property
    def handler_lock(self) -> RLock:
        return self._handler_lock

    def _log(
        self: SplatLogger,
        level: int,
        msg: Any,
        args,
        exc_info=None,
        extra: Optional[Mapping] = None,
        stack_info=False,
        **data,
    ) -> None:
        """
        Override to treat double-splat as a `"data"` extra.

        See `SplatLogger` doc for details.
        """

        if extra is not None:
            # This will fail if you give a non-`None` value that is not a
            # `Mapping` as `extra`, but it would have failed in
            # `logging.Logger.makeRecord` in that case anyways, so might as well
            # blow up here and save a cycle or two.
            extra = {"data": data, **extra}
        else:
            extra = {"data": data}

        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            stack_info=stack_info,
            extra=extra,
        )

    def iter_handlers(self) -> Generator[logging.Handler, None, None]:
        logger = self
        while logger:
            yield from logger.handlers
            if not logger.propagate:
                break
            else:
                logger = logger.parent

    def get_monitoring_handler_level(self):
        return min(
            (
                handler.level
                for handler in self.iter_handlers()
                if (
                    isinstance(handler, PriorityHandler)
                    and handler.level != logging.NOTSET
                )
            ),
            default=logging.NOTSET,
        )

    def getEffectiveLevel(self) -> int:
        """
        Get the effective level for this logger.

        Loop through this logger and its parents in the logger hierarchy,
        looking for a non-zero logging level. Return the first one found.
        """
        logger_level = super().getEffectiveLevel()
        monitoring_handler_level = self.get_monitoring_handler_level()

        # If _both_ the logger and handler level are not NOTSET (which is 0)
        # then we want the minimum between them
        if logger_level and monitoring_handler_level:
            return min(logger_level, monitoring_handler_level)

        # Otherwise at _least_ one of the logger and handler levels must be
        # NOTSET, so we want the maximum of the pair (which will still be
        # NOTSET if both are NOTSET)
        return max(logger_level, monitoring_handler_level)

    def removeHandler(self, hdlr: logging.Handler) -> None:
        """
        Overridden to clear `SplatLogger.console_handler` if that is the handler
        that is removed.
        """
        with self._handler_lock:
            super().removeHandler(hdlr)
            if hdlr is self.console_handler:
                del self.console_handler
            if hdlr is self.json_handler:
                del self.json_handler

    def addHandler(self, hdlr: logging.Handler) -> None:
        super().addHandler(hdlr)
        if isinstance(hdlr, PriorityHandler):
            hdlr.manager = self.manager
            self.manager._clear_cache()

    def inject(self, fn):
        @wraps(fn)
        def log_inject_wrapper(*args, **kwds):
            if "log" in kwds:
                return fn(*args, **kwds)
            else:
                return fn(*args, log=self.getChild(fn.__name__), **kwds)

        return log_inject_wrapper
