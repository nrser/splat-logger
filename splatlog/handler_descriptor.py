from contextlib import contextmanager, nullcontext
from logging import Logger, Handler
from typing import Optional, Type, TypeVar, Union, overload
from threading import RLock
from collections.abc import Mapping
from typeguard import get_type_name

from splatlog.levels import level_for
from splatlog.lib.typeguard import satisfies
from splatlog.typings import TLevelSetting

Self = TypeVar("Self", bound="HandlerDescriptor")
HandlerCastable = Union[None, bool, Handler, Mapping, TLevelSetting]

_NULL_CONTEXT = nullcontext()


class HandlerDescriptor:
    _name: Optional[str] = None
    _attr_name: Optional[str] = None
    _owner: Optional[Type[Logger]] = None

    def __init__(self, build):
        self._build = build

    @property
    def build(self):
        return self._build

    @contextmanager
    def sync(self, logger: Logger):
        with getattr(logger, "handler_lock", _NULL_CONTEXT):
            yield self.__get__(logger)

    def cast(self, logger: Logger, value: HandlerCastable) -> Optional[Handler]:
        if isinstance(value, Handler):
            return value

        if value is False or value is None:
            return None

        if value is True:
            return self.build(logger=logger)

        if isinstance(value, Mapping):
            return self.build(logger=logger, **value)

        if satisfies(value, TLevelSetting):
            return self.build(logger=logger, level=level_for(value))

        raise TypeError(
            "Expected {t_ex}, given {t_v}: {v}".format(
                t_ex=get_type_name(HandlerCastable),
                t_v=get_type_name(type(value)),
                v=repr(value),
            )
        )

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
            if current_handler is not None:
                logger.removeHandler(current_handler)
            logger.addHandler(handler)
            setattr(logger, self._attr_name, handler)

    def __delete__(self, logger: Logger) -> None:
        with self.sync(logger) as current_handler:
            if current_handler is not None:
                logger.removeHandler(current_handler)
                setattr(logger, self._attr_name, None)
