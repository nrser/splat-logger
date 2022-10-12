from __future__ import annotations
from io import StringIO
from typing import IO, TypeVar
from collections.abc import Generator
from splatlog.lib.collections import each

from splatlog.lib.collections.peek_iterator import (
    PeekIterator,
    PeekIteratorWrapper,
)
from splatlog.lib.validate.validator import Validator


_Self = TypeVar("_Self", bound="FailureGroup")


def format_failure_into(failures, dest: IO) -> None:
    for failure in failures:
        prefix = ()
        for groups, message in failure.items():
            if groups == prefix:
                print("    " * len(prefix), "-   ", message, file=dest)
            else:
                for index, group in enumerate(groups):
                    if index >= len(prefix) or prefix[index] != group:
                        print("    " * index, "-   ", group.name, file=dest)
                prefix = groups
                print("    " * len(prefix), "-   ", message, file=dest)


def format_failures(*failures):
    sio = StringIO()
    format_failure_into(failures, sio)
    return sio.getvalue()


def get_failures(value: object, *validators):
    return Failures(validator.validate() for validator in validators)


class FailureGroup(PeekIterator):
    _name: str
    _failures: tuple[PeekIterator, ...]

    def __init__(self, name: str, *failures):
        self._name = name
        self._failures = tuple(
            failure
            if isinstance(failure, PeekIterator)
            else PeekIteratorWrapper(failure)
            for failure in failures
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def failures(self) -> tuple[PeekIterator, ...]:
        return self._failures

    def is_empty(self) -> bool:
        return all(failure.is_empty() for failure in self._failures)

    def items(self):
        for failure in self._failures:
            for key_path, value in failure.items():
                yield ((self, *key_path), value)

    def __bool__(self) -> bool:
        return not self.is_empty()

    def __iter__(self) -> Generator[object, None, None]:
        for failure in self._failures:
            yield from failure

    def __repr__(self) -> str:
        return f"<FailureGroup {self._name!r}>"


class Failures(PeekIteratorWrapper):
    def items(self):
        for failure in self:
            if isinstance(failure, (self.__class__, FailureGroup)):
                yield from failure.items()
            else:
                yield ((), failure)

    def __repr__(self) -> str:
        if len(self._received) > 0:
            return f"<Failures [{self[0]!r}, ...]>"
        if self._stopped:
            return "<Failures []>"
        return "<Failures [..?]>"
