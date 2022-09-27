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
from collections.abc import Generator, Iterable
import sys

from splatlog.json.json_encoder import JSONEncoder
from splatlog.json.json_formatter import LOCAL_TIMEZONE, JSONFormatter
from splatlog.handler import PriorityHandler
from splatlog.rich_handler import RichHandler
from splatlog.typings import Level, LevelValue, ModuleType
from splatlog.handler_descriptor import (
    ConsoleHandlerDescriptor,
    FileHandlerDescriptor,
    HandlerDescriptor,
)


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

    console_handler = ConsoleHandlerDescriptor()
    file_handler = FileHandlerDescriptor()

    # _console_handler: Optional[RichHandler] = None
    _handler_lock: RLock
    _is_root: bool = False
    _role_name: Optional[str] = None
    _has_priority_handlers: bool = False

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

    def iterHandlers(self) -> Generator[logging.Handler, None, None]:
        logger = self
        while logger:
            yield from logger.handlers
            if not logger.propagate:
                break
            else:
                logger = logger.parent

    def getPriorityHandlerLevel(self):
        return min(
            (
                handler.level
                for handler in self.iterHandlers()
                if (
                    isinstance(handler, PriorityHandler)
                    and handler.level != logging.NOTSET
                )
            ),
            default=logging.NOTSET,
        )

    def getEffectiveLevel(self) -> LevelValue:
        """
        Get the effective level for this logger.

        Overridden from `logging.Logger.getEffectiveLevel` to take account of
        `PriorityHandler` instances
        """
        logger_level = super().getEffectiveLevel()
        priorityHandlerLevel = self.getPriorityHandlerLevel()

        # If _both_ the logger and handler level are not NOTSET (which is 0)
        # then we want the minimum between them
        if logger_level and priorityHandlerLevel:
            return min(logger_level, priorityHandlerLevel)

        # Otherwise at _least_ one of the logger and handler levels must be
        # NOTSET, so we want the maximum of the pair (which will still be
        # NOTSET if both are NOTSET)
        return max(logger_level, priorityHandlerLevel)

    def removeHandler(self, hdlr: logging.Handler) -> None:
        """
        Overridden to clear `SplatLogger.console_handler` if that is the handler
        that is removed.
        """
        with self._handler_lock:
            super().removeHandler(hdlr)

            if isinstance(hdlr, PriorityHandler):
                self.manager._clear_cache()

            if hdlr is self.console_handler:
                del self.console_handler

            if hdlr is self.file_handler:
                del self.file_handler

    def addHandler(self, hdlr: logging.Handler) -> None:
        super().addHandler(hdlr)
        if isinstance(hdlr, PriorityHandler):
            hdlr.manager = self.manager
            self.manager._clear_cache()

    def getEffectiveHandlerLevel(self, handler: logging.Handler) -> LevelValue:
        """
        Gets the _effective_ level for a `logging.Handler` with consideration
        for `PriorityHandler` support.

        The presence of a `PriorityHandler` may result in
        `SplatLogger.getEffectiveLevel` returning a value _lower_ than
        `logging.Logger.getEffectiveLevel` in order to let log records through
        to the `PriorityHandler`.

        This is easiest demonstrated by example.

        We start out by creating a logger for a library named "some_package".

        ```python
        >>> import sys
        >>> import logging
        >>> import splatlog

        >>> logger = splatlog.assignRole("some_package", "lib")

        ```

        The log level for this package is the default for library roles,
        `logging.WARNING`.

        ```python
        >>> logger.level == logging.WARNING
        True

        ```

        Next, we'll create a "regular" handler and add it to the logger. Note
        that the handler's level is the default of `logging.NOTSET`.

        ```python
        >>> regular_handler = logging.StreamHandler(sys.stdout)
        >>> regular_handler.level == logging.NOTSET
        True

        >>> logger.addHandler(regular_handler)

        ```

        At this point, `SplatLogger.getEffectiveLevel` behaves the same as
        `logging.Logger.getEffectiveLevel`, returning `logging.WARNING`.

        ```python
        >>> logger.getEffectiveLevel() == logging.WARNING
        True

        ```

        Now we create a "priority" handler with a `logging.DEBUG` level —
        meaning messages at _all_ standard log levels should be emitted,
        regardless of the logger's level — and add it to the logger.

        ```python
        >>> priority_handler = splatlog.PriorityStreamHandler(sys.stdout)
        >>> priority_handler.setLevel(logging.DEBUG)
        >>> logger.addHandler(priority_handler)

        ```

        Notice that now `SplatLogger.getEffectiveLevel` returns `logging.DEBUG`,
        reflecting the addition of the priority logger with a debug level.

        This is what allows priority loggers to receive records of the
        appropriate level.

        ```python
        >>> logger.getEffectiveLevel() == logging.DEBUG
        True

        ```

        However, we need some way to know what level our original "regular"
        handler should log at. That's where
        `SplatLogger.getEffectiveHandlerLevel` comes in — when called with the
        regular handler it returns the appropriate `logging.WARNING` level.

        ```python
        >>> logger.getEffectiveHandlerLevel(regular_handler) == logging.WARNING
        True

        ```

        Of course, when called on a `PriorityHandler`, the method simple returns
        the level of that handler (since they take _priority_).

        ```python
        >>> logger.getEffectiveHandlerLevel(priority_handler) == logging.DEBUG
        True

        ```

        This functionality is used in `SplatLogger.callHandlers` to decide which
        handlers to actually call.
        """
        if isinstance(handler, PriorityHandler):
            return handler.level
        return max(super().getEffectiveLevel(), handler.level)

    def callHandlers(self, record: logging.LogRecord) -> None:
        """
        Call `logging.Handler.handle` on the appropriate handlers for a
        `logging.LogRecord`.

        Overridden because `PriorityHandler` instances introduce a bit more
        complexity: we need to use `SplatLogger.getEffectiveHandlerLevel`
        instead of just looking at `logging.Handler.level`.

        See example in the `SplatLogger.getEffectiveHandlerLevel` doc.
        """

        found = 0
        for handler in self.iterHandlers():
            found = found + 1
            if record.levelno >= self.getEffectiveHandlerLevel(handler):
                handler.handle(record)

        if found == 0:
            if logging.lastResort:
                if record.levelno >= logging.lastResort.level:
                    logging.lastResort.handle(record)
            elif (
                logging.raiseExceptions
                and not self.manager.emittedNoHandlerWarning
            ):
                sys.stderr.write(
                    "No handlers could be found for logger"
                    ' "%s"\n' % self.name
                )
                self.manager.emittedNoHandlerWarning = True

    def inject(self, fn):
        @wraps(fn)
        def log_inject_wrapper(*args, **kwds):
            if "log" in kwds:
                return fn(*args, **kwds)
            else:
                return fn(*args, log=self.getChild(fn.__name__), **kwds)

        return log_inject_wrapper
