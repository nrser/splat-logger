from collections import namedtuple
from collections.abc import Container, Iterable
from io import StringIO
from typing import IO, Optional, Union
from functools import wraps

from .collections import each, group_by

SEQUENCE_TYPES = (list, tuple)

TFailure = tuple[tuple[str, ...], str]


class Validator(namedtuple("Validator", ("fn", "args", "kwds"))):
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


class ValidationFailure:
    pass


def format_failure_into(failure, dest: IO, depth=0) -> None:
    if isinstance(failure, tuple) and len(failure) == 2:
        key_path, values = failure
    else:
        key_path, values = (None, failure)

    key_path_list = list(each(key_path))

    for index, key in enumerate(key_path_list):
        dest.write("    " * (depth + index) + "-   " + str(key) + "\n")

    new_depth = depth + len(key_path_list)

    for value in each(values, deep=False):
        if isinstance(value, (list, tuple)):
            format_failure_into(value, dest, depth=new_depth)
        else:
            dest.write("    " * new_depth + "-   " + str(value) + "\n")


class ValidationError(Exception):
    @staticmethod
    def format_message(value, failures):
        sio = StringIO()
        sio.write(f"Value {value!r} failed to validate\n")
        for failure in failures:
            format_failure_into(failures, sio)
        return sio.getvalue()

        # lines = [f"Value {value!r} failed to validate"]

        # failures = sorted(failures)

        # prefix = ()
        # for key_path, message in failures:
        #     if key_path == prefix:
        #         lines.append("    " * len(prefix) + "-   " + message)
        #     else:
        #         for index, key in enumerate(key_path):
        #             if index >= len(prefix) or prefix[index] != key:
        #                 lines.append("    " * index + "-   " + str(key))
        #         prefix = key_path
        #         lines.append("    " * len(prefix) + "-   " + message)

        # return "\n".join(lines)

    failures: tuple[TFailure, ...]

    def __init__(self, value, failures: tuple[TFailure, ...]):
        super().__init__(ValidationError.format_message(value, failures))
        self.failures = failures


def _each(item_or_items):
    if isinstance(item_or_items, SEQUENCE_TYPES):
        for item in item_or_items:
            yield item
    else:
        yield item_or_items


def generate_failures(value, validators: Union[Validator, Iterable[Validator]]):
    if isinstance(validators, Validator):
        validators = (validators,)
    for fn, args, kwds in validators:
        yield from fn(value, *args, **kwds)


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
    return list(generate_failures(value, validators))


def is_valid(value, validators):
    return len(get_failures(value, validators)) == 0


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

    if len(failures) == 0:
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
        if len(failures) == 0:
            # One of the validators had no failures, so we're good
            return
        all_failures.extend(failures)
    yield ("Any of", all_failures)


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
def validate_attr(value, attrs, validator, message="`.{attr}`"):
    if not isinstance(validator, Validator):
        validator = validate(validator, message)
        message = "`.{attr}`"
    for attr in each(attrs):
        attr_value = getattr(value, attr)
        failures = get_failures(attr_value, validator)
        yield (message.format(attr=attr), failures)


@validator
def validate_attr_type(value, attrs, type, message="{attr} must be a {type!r}"):
    for attr in _each(attrs):
        if not isinstance(getattr(value, attr), type):
            yield (attr, message.format(attr=attr, type=type))


@validator
def validate_attr_in(
    value, attrs, container, message="{attr} must be in {container!r}"
):
    for attr in _each(attrs):
        if getattr(value, attr) not in container:
            yield ((attr,), message.format(attr=attr, container=container))
