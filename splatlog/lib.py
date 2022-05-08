from typing import Iterable, TypeVar, Union, Type, Generator

T = TypeVar("T")


def each(
    target: Union[T, Iterable[T]], value_type: Type[T]
) -> Generator[T, None, None]:
    if isinstance(target, value_type):
        yield target
    elif isinstance(target, Iterable):
        for item in target:
            yield item
    else:
        raise TypeError(
            f"Expected {value_type} or Iterable[{value_type}], given {type(target)}: {target!r}"
        )