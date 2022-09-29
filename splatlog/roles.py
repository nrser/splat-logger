"""
##### Examples #####

```python
>>> APP_ROLE.get_level(0) == INFO
True

>>> APP_ROLE.get_level(1) == DEBUG
True

>>> APP_ROLE.get_level(2) == DEBUG
True

```

"""

from dataclasses import dataclass
from functools import cached_property
from itertools import pairwise
from logging import DEBUG, INFO, NOTSET, WARNING
from typing import Optional, TypeVar
import sys

from splatlog.typings import LevelValue, Level, Verbosity


DEFAULT_ROLE_LEVEL = WARNING


TDefault = TypeVar("TDefault")
VerbosityLevel = tuple[Verbosity, LevelValue]
VerbosityRange = tuple[range, LevelValue]


@dataclass(frozen=True)
class Role:
    WILDCARD_NAME = "*"

    name: str
    verbosity_levels: tuple[VerbosityLevel, ...]
    default_level: Level = DEFAULT_ROLE_LEVEL
    description: Optional[str] = None
    is_builtin: bool = False

    def __post_init__(self):
        if self.name == "":
            raise ValueError("Role.name can not be the empty string")

        if self.name == self.__class__.WILDCARD_NAME:
            raise ValueError(
                "Role.name can not be {!r}".format(
                    self.__class__.WILDCARD_NAME,
                )
            )

    @cached_property
    def verbosity_ranges(self) -> tuple[VerbosityRange, ...]:
        return tuple(
            (range(v_1, v_2), l_1)
            for (v_1, l_1), (v_2, _) in pairwise(
                sorted(
                    (*self.verbosity_levels, (sys.maxsize, NOTSET)),
                    key=lambda vl: vl[0],
                )
            )
        )

    def get_level(self, verbosity: Optional[Verbosity]) -> LevelValue:
        if verbosity is None:
            return self.default_level
        for rng, level_value in self.verbosity_ranges:
            if verbosity in rng:
                return level_value
        return self.default_level


APP_ROLE = Role(
    name="app",
    description=None,
    verbosity_levels=(
        (0, INFO),
        (1, DEBUG),
    ),
    is_builtin=True,
)

SERVICE_ROLE = Role(
    name="service",
    description=None,
    verbosity_levels=(
        (0, WARNING),
        (1, INFO),
        (2, DEBUG),
    ),
)

LIB_ROLE = Role(
    name="lib",
    description=None,
    verbosity_levels=(
        (0, WARNING),
        (3, INFO),
        (4, DEBUG),
    ),
)
