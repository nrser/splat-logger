from __future__ import annotations
from collections.abc import Callable, Generator, Iterator, Container
from functools import wraps
from io import StringIO
from itertools import chain
from sys import stdout
from textwrap import wrap
from typing import (
    IO,
    Concatenate,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    overload,
    Iterable,
)
from splatlog.lib.collections import each, each_of
from splatlog.lib.collections.peek_iterator import PeekIteratorWrapper

from splatlog.lib.text import fmt

TParams = ParamSpec("TParams")
TReturn = TypeVar("TReturn")

Validator = Callable[[object], "Failures"]
ValidatorConstructor = Callable[TParams, Validator]


def _print_list_item(text, file, indent_level):
    indent = "    " * indent_level
    for line in wrap(
        text,
        width=80,
        initial_indent=(indent + "-   "),
        subsequent_indent=(indent + "    "),
        tabsize=4,
    ):
        print(line, file=file)


def print_failures(failures, file: IO = stdout) -> None:
    for failure in each_of(failures, Failures):
        prefix = ()
        for groups, message in failure.items():
            if groups == prefix:
                _print_list_item(message, file, len(prefix))
            else:
                for index, group in enumerate(groups):
                    if index >= len(prefix) or prefix[index] != group:
                        _print_list_item(group.name, file, index)
                prefix = groups
                _print_list_item(message, file, len(prefix))


def format_failures(*failures):
    sio = StringIO()
    print_failures(failures, sio)
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

    def __repr__(self) -> str:
        return str(self._name)

    @property
    def name(self) -> Optional[str]:
        return self._name

    def items(self):
        for failure in self:
            if isinstance(failure, self.__class__):
                if self._name is None:
                    yield from failure.items()
                else:
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
    failures = []
    for validator in validators:
        f = validator(value)
        if f.is_empty():
            return
        failures.append(f)
    return [("any of: {failures}", dict(failures=failures))]


@validator
def validate_all_of(value, *validators):
    return [validator(value) for validator in validators]


@validator
def validate(value, predicate, message):
    if not predicate(value):
        return [(message, None)]


@validator
def validate_in(
    value, container: Container, message: str = "must be in {container!r}"
):
    if value not in container:
        return [(message, dict(container=container))]


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
