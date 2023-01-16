from typing import Any, TypeGuard, TypeVar
from typeguard import check_type, TypeCheckError

T = TypeVar("T")


def satisfies(value: Any, expected_type: type[T]) -> TypeGuard[T]:
    try:
        check_type(value, expected_type)
    except TypeCheckError:
        return False
    return True
