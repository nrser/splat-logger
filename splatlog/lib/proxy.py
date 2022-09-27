from collections.abc import Collection, Iterator
from typing import TypeVar

T = TypeVar("T")


class CollectionProxy(Collection[T]):
    __slots__ = ("_target", "__weakref__")

    def __init__(self, target: Collection):
        self._target = target

    def __contains__(self, __x: object) -> bool:
        return __x in self._target

    def __len__(self) -> int:
        return len(self._target)

    def __iter__(self) -> Iterator[T]:
        return iter(self._target)
