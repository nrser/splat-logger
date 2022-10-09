from collections.abc import Iterator, Iterable
from typing import Optional, TypeVar
from abc import ABCMeta, abstractmethod

T = TypeVar("T")


class PeekIterator(Iterable[T]):
    @abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError("abstract")


class PeekIteratorWrapper(PeekIterator[T]):
    _iterator: Iterator[T]
    _received: list[T]
    _stopped: bool = False

    def __init__(self, iterator: Iterator[T]):
        self._iterator = iterator
        self._received = []

    def __getitem__(self, index: int) -> T:
        if index < 0:
            raise ValueError("negative indexes not supported, given {index!r}")

        received_length = len(self._received)

        if index < received_length:
            return self._received[index]

        if self._stopped:
            raise IndexError("index out of range")

        try:
            for _ in range(index - received_length + 1):
                self._received.append(next(self._iterator))
        except StopIteration:
            self._stopped = True
            raise IndexError("index out of range")

        return self._received[index]

    def is_empty(self) -> bool:
        if len(self._received) > 0:
            return False

        if self._stopped:
            return True

        try:
            self[0]
        except IndexError:
            return True
        return False

    def __iter__(self):
        for received in self._received:
            yield received

        if self._stopped:
            return

        try:
            while True:
                entry = next(self._iterator)
                self._received.append(entry)
                yield entry
        except StopIteration:
            self._stopped = True
