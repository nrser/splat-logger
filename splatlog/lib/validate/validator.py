import dataclasses
from collections.abc import Callable
from functools import wraps

from splatlog.lib.validate.failures import Failures


@dataclasses.dataclass(frozen=True, slots=True)
class Validator:
    fn: Callable
    args: tuple
    kwds: dict

    def validate(self, value: object):
        return Failures(self.fn(value, self.args, self.kwds))

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


def validator(fn):
    @wraps(fn)
    def _constructor(*args, **kwds):
        def _validator(value):
            return Failures(fn(value, *args, **kwds))

        return _validator

    return _constructor
