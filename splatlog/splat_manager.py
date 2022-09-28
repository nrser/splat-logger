from contextlib import contextmanager
from dataclasses import dataclass, replace
from functools import cached_property
from inspect import Parameter
from threading import RLock
from types import MappingProxyType
from typing import Optional, TypeVar, Union, overload
from collections.abc import Iterable, Mapping, Generator
from collections import defaultdict
import logging
from splatlog.handler_descriptor import (
    ConsoleHandlerDescriptor,
    FileHandlerDescriptor,
    HandlerDescriptor,
)

from typeguard import check_type

from splatlog.lib.collections import each

from splatlog.roles import Role
from splatlog.splat_logger import SplatLogger
from .rich_handler import RichHandler

from splatlog.typings import LevelValue, Level, Verbosity


DEFAULT_ROLE_LEVEL = logging.WARNING


TDefault = TypeVar("TDefault")
VerbosityLevel = tuple[Verbosity, LevelValue]
VerbosityRange = tuple[range, LevelValue]


class SplatManager:
    _roles: defaultdict[str, Role]
    _loggersByRole: dict[str, set[SplatLogger]]
    _handlersByRole: dict[str, set[logging.Handler]]
    _lock: RLock
    _verbosity: Optional[Verbosity] = None

    consoleHandler = ConsoleHandlerDescriptor()
    fileHandler = FileHandlerDescriptor()

    def __init__(self, builtin_roles: Iterable[Role] = ()):
        self._loggersByRole = defaultdict(set)
        self._handlersByRole = defaultdict(set)
        self._roles = {
            role.name: replace(role, is_builtin=True) for role in builtin_roles
        }
        self._lock = RLock()

    @property
    def handler_lock(self) -> RLock:
        return self._lock

    def getLogger(self, name: str) -> SplatLogger:
        logger = logging.getLogger(name)
        if not isinstance(logger, SplatLogger):
            raise TypeError(
                f"Expected SplatLogger, got {type(logger)}: {logger!r}"
            )
        return logger

    def setup(
        self,
        loggerName: Optional[str] = None,
        roleName: Optional[str] = None,
        *,
        verbosity: Optional[Verbosity] = None,
        console: Optional[logging.Handler] = RichHandler.default(),
        file: Optional[logging.Handler] = None,
        roleHandlers: Mapping[str, Iterable[logging.Handler]] = {},
    ) -> Optional[SplatLogger]:
        result = None

        if loggerName is not None and roleName is not None:
            result = self.assignRole(loggerName, roleName)

        if verbosity is not None:
            self.setVerbosity(verbosity)

        self.consoleHandler = console
        self.fileHandler = file

        for roleName, handlers in roleHandlers.items():
            for handler in handlers:
                self.addHandler(handler, role_name=roleName)

        return result

    # Verbosity
    # ========================================================================

    def getVerbosity(self) -> Optional[Verbosity]:
        return self._verbosity

    def setVerbosity(self, verbosity: Verbosity) -> None:
        if verbosity == self._verbosity:
            return

        self._verbosity = verbosity

        for role_name, loggers in self._loggersByRole.items():
            if role := self.getRole(role_name, None):
                level = role.get_level(verbosity)
                for logger in loggers:
                    logger.setLevel(level)

    def delVerbosity(self) -> None:
        if self._verbosity is not None:
            self._verbosity = None

            for role_name, loggers in self._loggersByRole.items():
                if role := self.getRole(role_name, None):
                    level = role.default_level
                    for logger in loggers:
                        logger.setLevel(level)

    verbosity = property(getVerbosity, setVerbosity, delVerbosity)

    # Role CRUD
    # ========================================================================

    @cached_property
    def roles(self) -> Mapping[str, Role]:
        return MappingProxyType(self._roles)

    def hasRole(self, name: str) -> bool:
        return name in self._roles

    @overload
    def getRole(self, name: str) -> Role:
        pass

    @overload
    def getRole(self, name: str, default: TDefault) -> Union[Role, TDefault]:
        pass

    def getRole(self, name, default=Parameter.empty):
        if default is Parameter.empty:
            return self._roles[name]
        return self._roles.get(name, default)

    def createRole(
        self,
        name: str,
        verbosity_levels: tuple[VerbosityLevel, ...],
        default_level: Level = DEFAULT_ROLE_LEVEL,
        description: Optional[str] = None,
    ) -> Role:
        role = Role(
            name=name,
            verbosity_levels=verbosity_levels,
            default_level=default_level,
            description=description,
            is_builtin=False,
        )

        if role.name in self._roles:
            raise KeyError(f"Role with name {name!r} already added")
        self._roles[role.name] = role

        return role

    def deleteRole(self, name: str):
        del self._roles[name]

    # Logger Roles
    # ========================================================================

    def getRoleLevel(self, role_name: str) -> Optional[LevelValue]:
        verbosity = self._verbosity

        if verbosity is None:
            return None

        role = self.getRole(role_name, None)

        if role is None:
            return None

        return role.get_level(verbosity)

    def assignRole(self, logger_name: str, role_name: str) -> SplatLogger:
        logger = self.getLogger(logger_name)

        if logger._role_name == role_name:
            return logger

        if logger._role_name is not None:
            raise AttributeError(
                "Logger {!r} already assigned role {!r}".format(
                    logger.name,
                    logger._role_name,
                )
            )

        logger._role_name = role_name
        self._loggersByRole[role_name].add(logger)

        if level := self.getRoleLevel(role_name):
            logger.setLevel(level)

        return logger

    def clearRole(self, logger_name: str):
        logger = self.getLogger(logger_name)
        current_role_name = logger._role_name

        if current_role_name is not None:
            self._loggersByRole[current_role_name].remove(logger)
            logger._role_name = None

            if level := self.getRoleLevel(current_role_name):
                logger.setLevel(level)

    def _iterLoggersForRole(
        self, role_name: str
    ) -> Generator[SplatLogger, None, None]:
        if role_name == Role.WILDCARD_NAME:
            for loggers in self._loggersByRole.values():
                yield from loggers
        else:
            if role_name in self._loggersByRole:
                yield from self._loggersByRole[role_name]

    # Handlers
    # ========================================================================

    def addHandler(
        self, handler: logging.Handler, *, role_name: str = Role.WILDCARD_NAME
    ) -> None:
        for logger in self._iterLoggersForRole(role_name):
            logger.addHandler(handler)

    def removeHandler(
        self, handler: logging.Handler, *, role_name: str = Role.WILDCARD_NAME
    ) -> None:
        if handler is self.consoleHandler:
            del self.consoleHandler
        elif handler is self.fileHandler:
            del self.fileHandler
        else:
            for logger in self._iterLoggersForRole(role_name):
                logger.removeHandler(handler)

    # Etc
    # ========================================================================

    @contextmanager
    def exclusiveContext(self):
        with self._lock:
            yield
