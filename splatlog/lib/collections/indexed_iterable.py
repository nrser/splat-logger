from typing import Protocol, TypeVar, runtime_checkable
from collections.abc import Iterator

T = TypeVar("T")


@runtime_checkable
class IndexedIterable(Protocol[T]):
    """
    ##### Examples #####

    ```python
    >>> isinstance([], IndexedIterable)
    True

    ```
    """

    def __iter__(self) -> Iterator[T]:
        ...

    def __getitem__(self, index: int) -> T:
        ...
