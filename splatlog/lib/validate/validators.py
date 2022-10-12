from itertools import chain
from typing import Optional
from collections.abc import Container

from splatlog.lib.collections import each
from splatlog.lib.validate.failures import FailureGroup, get_failures

from .validator import Validator, validator


# Validators
# ============================================================================

# Composers
# ----------------------------------------------------------------------------


@validator
def validate_when(value, predicate, *validators):
    """Only run `validators` when `predicate(value)` is "truthy"."""
    if predicate(value):
        yield from get_failures(value, *validators)


@validator
def validate_optional(value, *validators):
    """Run `validators` only when `value` is not `None`."""
    if value is not None:
        yield from get_failures(value, *validators)


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
    return Failures(*all_failures, name="Any of")


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


# @validator
# def validate_attr_type(value, attrs, type, message="{attr} must be a {type!r}"):
#     for attr in each(attrs):
#         if not isinstance(getattr(value, attr), type):
#             yield (attr, message.format(attr=attr, type=type))


# @validator
# def validate_attr_in(
#     value, attrs, container, message="{attr} must be in {container!r}"
# ):
#     for attr in each(attrs):
#         if getattr(value, attr) not in container:
#             yield ((attr,), message.format(attr=attr, container=container))
