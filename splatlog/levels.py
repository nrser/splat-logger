import logging
from typing import Any, Dict, Optional, Set, Tuple, cast

from splatlog.typings import (
    ModuleType,
    LevelValue,
    LevelName,
    TLevelSetting,
    Verbosity,
)

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

# Default for applications — the things you actually run / use.
DEFAULT_APP_LEVEL = INFO

# Default for libraries — things used by applications or other libraries.
DEFAULT_LIB_LEVEL = WARNING

# Map of log levels... by (constant) name.
LEVELS_BY_NAME: Dict[LevelName, LevelValue] = dict(
    CRITICAL=CRITICAL,
    FATAL=FATAL,
    ERROR=ERROR,
    WARNING=WARNING,
    INFO=INFO,
    DEBUG=DEBUG,
    NOTSET=NOTSET,
)

LEVEL_SET: Set[LevelValue] = set(LEVELS_BY_NAME.values())


def default_level_for(module_type: ModuleType) -> LevelValue:
    if module_type is ModuleType.APP:
        return DEFAULT_APP_LEVEL
    if module_type is ModuleType.LIB:
        return DEFAULT_LIB_LEVEL
    raise ValueError(
        f"Unexpected `module_type` value {module_type!r}, "
        + f"expected {ModuleType.APP} or {ModuleType.LIB}"
    )


def resolve_level_value(
    setting: Optional[TLevelSetting], module_type: ModuleType
) -> LevelValue:
    if setting is None:
        return default_level_for(module_type)
    return level_for(setting)


def level_for(setting: TLevelSetting) -> LevelValue:
    """
    Make a `logging` level number from more useful/intuitive things, like string
    you might get from an environment variable or command option.

    Examples:

    1.  Integer levels can be provided as strings:

            >>> level_for("10")
            10

    2.  Levels we don't know get a puke:

            >>> level_for("8")
            Traceback (most recent call last):
                ...
            ValueError: Unknown log level integer 8; known levels are 50 (CRITICAL), 50 (FATAL), 40 (ERROR), 30 (WARNING), 30 (WARN), 20 (INFO), 10 (DEBUG) and 0 (NOTSET)

    3.  We also accept level *names* (gasp!), case-insensitive:


            >>> level_for("debug")
            10
            >>> level_for("DEBUG")
            10
            >>> level_for("Debug")
            10

    4.  Everything else can kick rocks:

            >>> level_for([])
            Traceback (most recent call last):
                ...
            TypeError: Expected `value` to be `str` or `int`, given `list`: []
    """

    if isinstance(setting, str):
        if setting.isdigit():
            return level_for(int(setting))
        upper_case_value = setting.upper()
        if upper_case_value in LEVELS_BY_NAME:
            return LEVELS_BY_NAME[upper_case_value]
        raise ValueError(
            f"Unknown log level name {repr(setting)}; known level names are "
            f"{', '.join(LEVELS_BY_NAME.keys())} (case-insensitive)"
        )
    if isinstance(setting, int):
        if setting in LEVEL_SET:
            return cast(LevelValue, setting)
        levels = ", ".join(f"{v} ({k})" for k, v in LEVELS_BY_NAME.items())
        raise ValueError(
            f"Unknown log level integer {setting}; known levels are {levels}"
        )
    raise TypeError(
        f"Expected `value` to be `str` or `int`, given {type(setting)}: {setting!r}"
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
