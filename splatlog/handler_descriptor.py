from contextlib import contextmanager, nullcontext
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, Logger, Handler
from pathlib import Path
import sys
from typing import IO, Optional, Type, TypeVar, Union, overload
from collections.abc import Mapping

from rich.console import Console

from splatlog.handler.priority_handler import PriorityFileHandler
from splatlog.json.json_encoder import JSONEncoder
from splatlog.json.json_formatter import JSONFormatter
from splatlog.rich_handler import RichHandler
from splatlog.levels import level_for
from splatlog.lib.typeguard import satisfies
from splatlog.typings import Level, TLevelSetting

Self = TypeVar("Self", bound="HandlerDescriptor")
HandlerCastable = Union[None, bool, Handler, Mapping, TLevelSetting]

_NULL_CONTEXT = nullcontext()


class HandlerDescriptor:
    _name: Optional[str] = None
    _attr_name: Optional[str] = None
    _owner: Optional[Type[Logger]] = None

    @contextmanager
    def sync(self, logger: Logger):
        with getattr(logger, "handler_lock", _NULL_CONTEXT):
            yield self.__get__(logger)

    def cast(self, logger: Logger, value: HandlerCastable) -> Optional[Handler]:
        raise NotImplementedError()

    # Descriptor Protocol
    # ========================================================================

    def __set_name__(self, owner: Type[Logger], name: str) -> None:
        self._owner = owner
        self._name = name
        self._attr_name = f"_{name}"

    @overload
    def __get__(
        self, logger: None, owner: Optional[Type[Logger]] = None
    ) -> Self:
        pass

    @overload
    def __get__(
        self, logger: Logger, owner: Optional[Type[Logger]] = None
    ) -> Optional[Handler]:
        pass

    def __get__(self, logger, owner=None):
        # When accessed as a class attribute return the descriptor itself
        if logger is None:
            return self

        return getattr(logger, self._attr_name, None)

    def __set__(self, logger: Logger, value: HandlerCastable) -> None:
        handler = self.cast(logger, value)

        with self.sync(logger) as current_handler:
            if current_handler is not handler:
                setattr(logger, self._attr_name, handler)
                if current_handler is not None:
                    logger.removeHandler(current_handler)
                logger.addHandler(handler)

    def __delete__(self, logger: Logger) -> None:
        with self.sync(logger) as current_handler:
            if current_handler is not None:
                setattr(logger, self._attr_name, None)
                logger.removeHandler(current_handler)


class ConsoleHandlerDescriptor(HandlerDescriptor):
    def cast(self, logger, value):
        if value is None or isinstance(value, Handler):
            return value

        if isinstance(value, Mapping):
            return RichHandler(**value)

        if satisfies(value, Level):
            return RichHandler(level=level_for(value))

        if value is sys.stdout:
            return RichHandler(
                level_map={
                    CRITICAL: "out",
                    ERROR: "out",
                    WARNING: "out",
                    INFO: "out",
                    DEBUG: "out",
                }
            )

        if value is sys.stderr:
            return RichHandler(
                level_map={
                    CRITICAL: "err",
                    ERROR: "err",
                    WARNING: "err",
                    INFO: "err",
                    DEBUG: "err",
                }
            )

        if satisfies(value, IO):
            return RichHandler(
                consoles={
                    "custom": Console(
                        file=value, theme=RichHandler.DEFAULT_THEME
                    )
                },
                level_map={
                    CRITICAL: "custom",
                    ERROR: "custom",
                    WARNING: "custom",
                    INFO: "custom",
                    DEBUG: "custom",
                },
            )

        raise TypeError(
            "Expected {}, given {}: {!r}".format(
                Union[None, Handler, Mapping, Level], type(value), value
            )
        )


class FileHandlerDescriptor(HandlerDescriptor):
    def cast(self, logger, value):
        if value is None or isinstance(value, Handler):
            return value

        if isinstance(value, Mapping):
            handler = PriorityFileHandler(
                **{k: v for k, v in value.items() if k != "formatter"}
            )

            if "formatter" in value:
                formatter_kwds = {
                    k: v
                    for k, v in value["formatter"].items()
                    if k != "encoder"
                }

                if "encoder" in value["formatter"]:
                    formatter_kwds["encoder"] = JSONEncoder(
                        **value["formatter"]["encoder"]
                    )

                handler.formatter = JSONFormatter(**formatter_kwds)

            else:
                handler.formatter = JSONFormatter()

            return handler

        if isinstance(value, (str, Path)):
            handler = PriorityFileHandler(filename=value)
            handler.formatter = JSONFormatter()
            return handler

        raise TypeError(
            "Expected {}, given {}: {!r}".format(
                Union[None, Handler, Mapping, str, Path], type(value), value
            )
        )
