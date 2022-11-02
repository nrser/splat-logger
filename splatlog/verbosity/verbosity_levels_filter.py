"""The `VerbosityLevelsFilter` class."""

import logging
from typing import Optional
from splatlog.names import is_in_hierarchy

from splatlog.verbosity.verbosity_state import (
    VerbosityLevels,
    VerbosityLevelsCastable,
    cast_verbosity_levels,
    get_verbosity,
)

__all__ = ["VerbosityLevelsFilter"]


class VerbosityLevelsFilter(logging.Filter):
    """A `logging.Filter` that filters based on
    `splatlog.typings.VerbosityLevels` and the current (global)
    `splatlog.typings.Verbosity` value

    ##### See Also #####

    1.  `splatlog.verbosity.verbosity_state.get_verbosity`

    ##### Examples #####

    Here we create a filter that applies to a `some_module` logger (and all it's
    descendant loggers).

    ```python
    >>> from splatlog._testing import make_log_record
    >>> import splatlog

    >>> filter = VerbosityLevelsFilter(
    ...     {
    ...         "some_module": (
    ...             (0, "WARNING"),
    ...             (2, "INFO"),
    ...             (4, "DEBUG"),
    ...         )
    ...     }
    ... )

    ```

    When verbosity is not set everything is allowed through.

    ```python
    >>> splatlog.del_verbosity()
    >>> filter.filter(make_log_record(name="some_module", level="WARNING"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="INFO"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="DEBUG"))
    True

    ```

    Once verbosity is set the filter takes effect.

    ```python
    >>> splatlog.set_verbosity(0)
    >>> filter.filter(make_log_record(name="some_module", level="WARNING"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="INFO"))
    False
    >>> filter.filter(make_log_record(name="some_module", level="DEBUG"))
    False

    >>> splatlog.set_verbosity(2)
    >>> filter.filter(make_log_record(name="some_module", level="WARNING"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="INFO"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="DEBUG"))
    False

    >>> splatlog.set_verbosity(8)
    >>> filter.filter(make_log_record(name="some_module", level="WARNING"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="INFO"))
    True
    >>> filter.filter(make_log_record(name="some_module", level="DEBUG"))
    True

    ```

    Descendant loggers follow the same logic.

    ```python
    >>> splatlog.set_verbosity(1)
    >>> filter.filter(make_log_record(name="some_module.blah", level="INFO"))
    False

    ```

    Loggers that are not descendants are all allowed through.

    ```python
    >>> splatlog.set_verbosity(1)
    >>> filter.filter(make_log_record(name="other_module", level="INFO"))
    True

    ```
    """

    @classmethod
    def get_from(cls, filterer: logging.Filterer):
        for filter in filterer.filters:
            if isinstance(filter, cls):
                return filter

    @classmethod
    def set_on(
        cls,
        filterer: logging.Filterer,
        verbosity_levels: Optional[VerbosityLevelsCastable],
    ) -> None:
        cls.remove_from(filterer)

        if verbosity_levels is None:
            return

        filter = cls(verbosity_levels)

        filterer.addFilter(filter)

    @classmethod
    def remove_from(cls, filterer: logging.Filterer):
        for filter in [f for f in filterer.filters if isinstance(f, cls)]:
            filterer.removeFilter(filter)

    _verbosity_levels: VerbosityLevels

    def __init__(self, verbosity_levels: VerbosityLevelsCastable):
        super().__init__()
        self._verbosity_levels = cast_verbosity_levels(verbosity_levels)

    @property
    def verbosity_levels(self) -> VerbosityLevels:
        return self._verbosity_levels

    def filter(self, record: logging.LogRecord) -> bool:
        if self._verbosity_levels is None:
            return True

        verbosity = get_verbosity()

        if verbosity is None:
            return True

        for hierarchy_name, ranges in self._verbosity_levels.items():
            if is_in_hierarchy(hierarchy_name, record.name):
                effectiveLevel = ranges.get_level(verbosity)
                return (
                    effectiveLevel is None or record.levelno >= effectiveLevel
                )

        return True
