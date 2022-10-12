from collections import namedtuple
from collections.abc import Container, Iterable, Generator, Iterator, Callable
import dataclasses
from io import StringIO
from itertools import chain
from typing import (
    IO,
    Any,
    Concatenate,
    Generic,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
)
from functools import wraps

from splatlog.lib.collections import each
from splatlog.lib.collections.peek_iterator import PeekIterator
from splatlog.lib.validate.failures import FailureGroup, format_failure_into
from splatlog.lib.validate.validator import Validator

SEQUENCE_TYPES = (list, tuple)

Failure = object


class ValidationError(Exception):
    @staticmethod
    def format_message(value, failures):
        sio = StringIO()
        sio.write(f"Value {value!r} failed to validate\n")
        format_failure_into(failures, sio)
        return sio.getvalue()

    failures: tuple

    def __init__(self, value, failures: tuple):
        super().__init__(ValidationError.format_message(value, failures))
        self.failures = failures


def generate_failures(value, validators: Union[Validator, Iterable[Validator]]):
    if isinstance(validators, Validator):
        validators = (validators,)
    for validator in validators:
        yield from validator.validate(value)


def run_validators(value, *validators):
    yield from generate_failures(value, (v for v in validators if v))


def get_failures(value, validators):
    """Get a `tuple` of validation failures.

    ##### Examples #####

    ```python

    >>> get_failures(
    ...     123,
    ...     validate(lambda v: v > 0, "Is positive"),
    ... )
    []

    ```

    ```python

    >>> get_failures(
    ...     123,
    ...     validate(lambda v: v < 0, "Must be negative"),
    ... )
    ['Must be negative']

    ```

    ```python

    >>> from pathlib import Path
    >>> get_failures(
    ...     Path.cwd(),
    ...     validate_attr(
    ...         ("name", "suffix"),
    ...         lambda v: v == "not_gonna_happen",
    ...         "must be 'not_gonna_happen'"
    ...     ),
    ... )
    [('`.name`', ["must be 'not_gonna_happen'"]),
        ('`.suffix`', ["must be 'not_gonna_happen'"])]

    ```

    ```python

    >>> get_failures(
    ...     11,
    ...     validate_any_of(
    ...         validate_in(range(10)),
    ...         validate(lambda x: x % 2 == 0, "Must be even"),
    ...     )
    ... )
    [('Any of', ['Must be in range(0, 10)', 'Must be even'])]

    ```

    ```python
    >>> get_failures(
    ...     Path.cwd(),
    ...     validate_attr(
    ...         "name",
    ...         validate_any_of(
    ...             validate_length(max=0),
    ...             validate(
    ...                 lambda v: v == "not_gonna_happen",
    ...                 "must be 'not_gonna_happen'"
    ...             ),
    ...         )
    ...     )
    ... )
    [('`.name`',
        [('Any of',
            ['Length must be at most 0',
             "must be 'not_gonna_happen'"])])]

    ```

    ```python
    >>> get_failures(
    ...     Path.cwd(),
    ...     validate_any_of(
    ...         validate_attr(
    ...             "name",
    ...             validate_length(max=0),
    ...         ),
    ...         validate_attr(
    ...             "suffix",
    ...             validate(
    ...                 lambda v: v == "not_gonna_happen",
    ...                 "must be 'not_gonna_happen'"
    ...             ),
    ...         ),
    ...     ),
    ... )
    [('Any of',
        [('`.name`', ['Length must be at most 0']),
         ('`.suffix`', ["must be 'not_gonna_happen'"])])]

    ```

    # ```python
    # >>> get_failures(
    # ...     Path.cwd(),
    # ...     validate_attr(
    # ...         "name",
    # ...         validate_length(min=0)
    # ...         | validate(lambda p: False, "Must not be bad"),
    # ...     )
    # ... )

    # ```

    """
    return Failures(generate_failures(value, validators))


def is_valid(value, validators):
    return get_failures(value, validators).is_empty()


def check_valid(value, validators) -> None:
    """Raise an error if `value` does not validate.

    ```python

    >>> check_valid(255, validate_in(range(2 ** 8))) is None
    True

    >>> check_valid(256, validate_in(range(2 ** 8)))
    Traceback (most recent call last):
        ...
    splatlog.lib.validate.ValidationError: Value 256 failed to validate
    -   Must be in range(0, 256)

    >>> from pathlib import Path

    >>> check_valid(
    ...     Path("/a/b/c"),
    ...     validate_any_of(
    ...         validate_attr(
    ...             "name",
    ...             validate_length(max=0),
    ...         ),
    ...         validate_attr(
    ...             "suffix",
    ...             validate(
    ...                 lambda v: v == "not_gonna_happen",
    ...                 "must be 'not_gonna_happen'"
    ...             ),
    ...         ),
    ...     ),
    ... )
    Traceback (most recent call last):
        ...
    splatlog.lib.validate.ValidationError: Value PosixPath('/a/b/c') failed to validate
    -   Any of
        -   `.name`
            -   Length must be at most 0
        -   `.suffix`
            -   must be 'not_gonna_happen'n

    ```
    """
    failures = get_failures(value, validators)

    if failures.is_empty():
        return

    raise ValidationError(value, failures)
