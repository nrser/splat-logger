from typing import Any, Type, TypeGuard, TypeVar
from typeguard import check_type

T = TypeVar("T")


def satisfies(value: Any, expected_type: Type[T]) -> TypeGuard[T]:
    try:
        check_type("value", value, expected_type)
    except TypeError:
        return False
    return True
