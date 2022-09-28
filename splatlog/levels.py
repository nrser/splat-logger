import logging
from typing import Dict, Set, cast

from splatlog.lib.text import fmt
from splatlog.typings import Level, LevelValue, LevelName

# Re-defining log levels allows using this module to be swapped in for basic
# uses of stdlib `logging`.
CRITICAL = logging.CRITICAL  # 50
FATAL = logging.FATAL  # ↑
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
WARN = logging.WARN  # ↑
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10
NOTSET = logging.NOTSET  # 0

# Map of log levels... by (constant) name.
LEVELS_BY_NAME: Dict[LevelName, LevelValue] = dict(
    CRITICAL=CRITICAL,
    FATAL=FATAL,
    ERROR=ERROR,
    WARNING=WARNING,
    WARN=WARNING,
    INFO=INFO,
    DEBUG=DEBUG,
    NOTSET=NOTSET,
)

LEVEL_SET: Set[LevelValue] = set(LEVELS_BY_NAME.values())


def getLevelValue(level: Level) -> LevelValue:
    """
    Make a `logging` level number from more useful/intuitive things, like string
    you might get from an environment variable or command option.

    Examples:

    1.  Integer levels can be provided as strings:

            >>> getLevelValue("10")
            10

    2.  Levels we don't know get a puke:

            >>> getLevelValue("8")
            Traceback (most recent call last):
                ...
            ValueError: Unknown log level integer 8; known levels are 50
                (CRITICAL), 50 (FATAL), 40 (ERROR), 30 (WARNING), 30 (WARN),
                20 (INFO), 10 (DEBUG), 0 (NOTSET)

    3.  We also accept level *names* (gasp!), case-insensitive:


            >>> getLevelValue("debug")
            10
            >>> getLevelValue("DEBUG")
            10
            >>> getLevelValue("Debug")
            10

    4.  Everything else can kick rocks:

            >>> getLevelValue([])
            Traceback (most recent call last):
                ...
            TypeError: Expected `level` to be `int | str`, given `list`: []
    """

    if isinstance(level, str):
        if level.isdigit():
            return getLevelValue(int(level))
        upper_case_value = level.upper()
        if upper_case_value in LEVELS_BY_NAME:
            return LEVELS_BY_NAME[upper_case_value]
        raise ValueError(
            f"Unknown log level name {repr(level)}; known level names are "
            f"{', '.join(LEVELS_BY_NAME.keys())} (case-insensitive)"
        )
    if isinstance(level, int):
        if level in LEVEL_SET:
            return cast(LevelValue, level)
        levels = ", ".join(f"{v} ({k})" for k, v in LEVELS_BY_NAME.items())
        raise ValueError(
            f"Unknown log level integer {level}; known levels are {levels}"
        )
    raise TypeError(
        "Expected `level` to be `{}`, given `{}`: {}".format(
            fmt(Level), fmt(type(level)), fmt(level)
        )
    )
