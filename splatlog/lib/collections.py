from typing import TypeVar, Union, Type, overload
from collections.abc import Callable, Iterable, Generator, Mapping, Container


T = TypeVar("T")
TEntry = TypeVar("TEntry")
TNotFound = TypeVar("TNotFound")
TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


def find(
    predicate: Callable[[TEntry], bool],
    iterable: Iterable[TEntry],
    *,
    not_found: TNotFound = None,
) -> Union[TEntry, TNotFound]:
    for entry in iterable:
        if predicate(entry):
            return entry
    return not_found


def each(
    target: Union[None, T, Iterable[T]], value_type: Type[T]
) -> Generator[T, None, None]:
    if target is None:
        return
    if isinstance(target, value_type):
        yield target
    elif isinstance(target, Iterable):
        for item in target:
            yield item
    else:
        raise TypeError(
            f"Expected {value_type} or Iterable[{value_type}], "
            + f"given {type(target)}: {target!r}"
        )


def partition_mapping(
    mapping: Mapping[TKey, TValue],
    by: Union[Container, Callable[[TKey], bool]],
) -> tuple[dict[TKey, TValue], dict[TKey, TValue]]:
    """
    ##### Examples #####

    ```python
    >>> partition_mapping(
    ...     {"a": 1, "b": 2, "c": 3, "d": 4},
    ...     {"a", "c"}
    ... )
    ({'a': 1, 'c': 3}, {'b': 2, 'd': 4})

    ```
    """
    if isinstance(by, Container):
        by = by.__contains__
    inside = {}
    outside = {}
    for key, value in mapping.items():
        if by(key):
            inside[key] = value
        else:
            outside[key] = value
    return (inside, outside)
