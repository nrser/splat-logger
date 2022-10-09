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
from splatlog.lib.validate.failures import FailureGroup

SEQUENCE_TYPES = (list, tuple)

TFailure = tuple[tuple[str, ...], str]

###

Failure = object

# TParams = ParamSpec("TParams")
# TReturn = TypeVar("TReturn")

# ValidationFn = Callable[Concatenate[object, TParams], TReturn]


@dataclasses.dataclass(frozen=True, slots=True)
class Validator:
    fn: Callable
    args: tuple
    kwds: dict

    def validate(self, value: object):
        return self.fn(value, self.args, self.kwds)

    def __repr__(self) -> str:
        # Validator( validate_any_of( Validator( validate_in( range(0, 10 ) )) ))
        #
        # Validator( validate_any_of, Validator( validate_in, range(0, 10 ) ) )

        inside = ", ".join(
            (
                self.fn.__qualname__,
                *(repr(v) for v in self.args),
                *(f"{k}={v!r}" for k, v in self.kwds.items()),
            )
        )
        return f"{self.__class__.__qualname__}( {inside} )"


class Failures(PeekIterator[Failure]):
    pass


def format_failure_into(failures, dest: IO, depth=0) -> None:
    if isinstance(failures, FailureGroup):
        for index, key in enumerate(each(failures.name)):
            dest.write("    " * (depth + index) + "-   " + str(key) + "\n")
            depth += 1

    for failure in failures:
        if isinstance(failure, FailureGroup):
            format_failure_into(failure, dest, depth=depth)
        else:
            dest.write("    " * depth + "-   " + str(failure) + "\n")


def format_failures(*failures):
    sio = StringIO()
    format_failure_into(failures, sio)
    return sio.getvalue()


class ValidationError(Exception):
    @staticmethod
    def format_message(value, failures):
        sio = StringIO()
        sio.write(f"Value {value!r} failed to validate\n")
        format_failure_into(failures, sio)
        return sio.getvalue()

    failures: tuple[TFailure, ...]

    def __init__(self, value, failures: tuple[TFailure, ...]):
        super().__init__(ValidationError.format_message(value, failures))
        self.failures = failures


def generate_failures(value, validators: Union[Validator, Iterable[Validator]]):
    if isinstance(validators, Validator):
        validators = (validators,)
    for validator in validators:
        yield from validator.validate(value)


def run_validators(value, *validators):
    yield from generate_failures(value, (v for v in validators if v))


def simplify(sequence):
    length = len(sequence)
    if length == 0:
        return None
    if length == 1:
        return sequence[0]


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


def validator(fn):
    @wraps(fn)
    def constructor(*args, **kwds):
        return Validator(fn, args, kwds)

    return constructor


# Validator Composers
# ============================================================================


@validator
def validate_when(value, predicate, *validators):
    """Only run `validators` when `predicate(value)` is "truthy"."""
    if predicate(value):
        yield from generate_failures(value, validators)


@validator
def validate_optional(value, *validators):
    """Run `validators` only when `value` is not `None`."""
    if value is not None:
        yield from generate_failures(value, validators)


@validator
def validate_any_of(value, *validators):
    """Hey now!

    If any of the validators pass, `validate_any_of` passes:

    ```python

    >>> check_valid(
    ...     1,
    ...     validate_any_of(
    ...         validate_in(range(10)),
    ...         validate(lambda x: x % 2 == 0, "Must be even"),
    ...     )
    ... ) is None
    True

    ```

    All of the validators must fail for `validate_any_of` to fail:

    ```python

    >>> check_valid(
    ...     11,
    ...     validate_any_of(
    ...         validate_in(range(10)),
    ...         validate(lambda x: x % 2 == 0, "Must be even"),
    ...     )
    ... )
    Traceback (most recent call last):
      ...
    splatlog.lib.validate.ValidationError: Value 11 failed to validate
    -   Any of
        -   Must be in range(0, 10)
        -   Must be even

    ```
    """
    all_failures = []
    for validator in validators:
        failures = get_failures(value, validator)
        if failures.is_empty():
            return
        all_failures.append(failures)
    yield FailureGroup("Any of", chain.from_iterable(all_failures))


# Validators
# ============================================================================


@validator
def validate(value, predicate, message):
    if not predicate(value):
        yield message


@validator
def validate_in(
    value, container: Container, message: str = "Must be in {container!r}"
):
    if value not in container:
        yield message.format(container=container)


@validator
def validate_min(
    value,
    min,
    message: str = "Must be {conditional} than {min}",
    exclusive: bool = False,
):
    if exclusive:
        if value <= min:
            yield message.format(min=min, conditional="greater than")
    else:
        if value < min:
            yield message.format(
                min=min, conditional="greater than or equal to"
            )


@validator
def validate_length(
    value,
    min: Optional[int] = None,
    max: Optional[int] = None,
    message: Optional[str] = None,
):
    if min is not None and max is not None and min > max:
        raise ValueError(
            f"When both `min` and `max` are given, `min` must be greater "
            + "or equal to `max`; given min={min!r}, max={max!r}"
        )

    length = len(value)

    if min is not None and length < min:
        yield f"Length must be at least {min}"

    if max is not None and length > max:
        yield f"Length must be at most {max}"


# Attribute Validators
# ----------------------------------------------------------------------------


@validator
def validate_attr(value, attrs, validator, message=None, *, name="`.{attr}`"):
    if not isinstance(validator, Validator):
        validator = validate(validator, message)
    for attr in each(attrs):
        attr_value = getattr(value, attr)
        yield FailureGroup(
            name.format(attr=attr), get_failures(attr_value, validator)
        )


@validator
def validate_attr_type(value, attrs, type, message="{attr} must be a {type!r}"):
    for attr in each(attrs):
        if not isinstance(getattr(value, attr), type):
            yield (attr, message.format(attr=attr, type=type))


@validator
def validate_attr_in(
    value, attrs, container, message="{attr} must be in {container!r}"
):
    for attr in each(attrs):
        if getattr(value, attr) not in container:
            yield ((attr,), message.format(attr=attr, container=container))
