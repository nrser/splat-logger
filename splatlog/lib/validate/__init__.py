from __future__ import annotations
from collections.abc import Callable, Generator, Iterator, Container
from functools import wraps
from io import StringIO
from itertools import chain
from typing import IO, Concatenate, Optional, ParamSpec, TypeVar, Union
from splatlog.lib.collections import each
from splatlog.lib.collections.peek_iterator import PeekIteratorWrapper

from splatlog.lib.text import fmt

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")

Validator = Callable[[object], "Failures"]
ValidatorConstructor = Callable[TParams, Validator]


def format_failure_into(failures, dest: IO) -> None:
    for failure in failures:
        prefix = ()
        for groups, message in failure.items():
            if groups == prefix:
                print("    " * len(prefix), "-   ", message, file=dest)
            else:
                for index, group in enumerate(groups):
                    if index >= len(prefix) or prefix[index] != group:
                        print("    " * index, "-   ", group.name, file=dest)
                prefix = groups
                print("    " * len(prefix), "-   ", message, file=dest)


def format_failures(*failures):
    sio = StringIO()
    format_failure_into(failures, sio)
    return sio.getvalue()


class Failures(PeekIteratorWrapper):
    _name: Optional[str]

    def __init__(self, *targets, name: Optional[str] = None):
        if len(targets) == 1:
            iterator = targets[0]
        else:
            iterator = chain.from_iterable(targets)

        super().__init__(iterator)
        self._name = name

    @property
    def name(self) -> Optional[str]:
        return self._name

    def items(self):
        for failure in self:
            if isinstance(failure, self.__class__):
                for key_path, value in failure.items():
                    yield ((self, (key_path)), value)
            elif self._name is None:
                yield ((), failure)
            else:
                yield ((self,), failure)


EMPTY_FAILURES = Failures(iter(()))


def validator(
    f: Callable[Concatenate[object, TParams], Union[Failures, Generator]]
) -> ValidatorConstructor[TParams]:
    @wraps(f)
    def validator_constructor(
        *args: TParams.args, **kwargs: TParams.kwargs
    ) -> Validator:
        def validate(value: object) -> Failures:
            result = f(value, *args, **kwargs)

            if result is None:
                return EMPTY_FAILURES

            if isinstance(result, Failures):
                return result

            if isinstance(result, Generator):
                return Failures(result)

            raise TypeError(
                (
                    "expected validator to return `{}`, "
                    "received `{}`\n\n    {}"
                ).format(
                    fmt(Union[Failures, Generator]),
                    fmt(type(result)),
                    fmt(result),
                )
            )

        return validate

    return validator_constructor


# Validators
# ============================================================================

# Composers
# ----------------------------------------------------------------------------


@validator
def validate_when(value, predicate, validator):
    """Only run `validators` when `predicate(value)` is "truthy"."""
    if predicate(value):
        return validator(value)


@validator
def validate_optional(value, validator):
    """Run `validators` only when `value` is not `None`."""
    if value is not None:
        return validator(value)


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
        failures = validator(value)
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
def validate_attr(value, attrs, validator, *, name="`.{attr}`"):
    for attr in each(attrs):
        attr_value = getattr(value, attr)
        yield Failures(validator(attr_value), name=name.format(attr=attr))
