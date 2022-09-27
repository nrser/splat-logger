from typing import Literal, TypeVar, Union, Type, overload
from collections.abc import Callable, Iterable, Generator


T = TypeVar("T")
TEntry = TypeVar("TEntry")
TNotFound = TypeVar("TNotFound")


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
