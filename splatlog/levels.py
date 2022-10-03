import logging

from splatlog.lib.text import fmt
from splatlog.typings import Level, LevelValue

# Alias the standard `logging` levels so you can avoid another import in many
# cases
CRITICAL = logging.CRITICAL  # 50
FATAL = logging.FATAL  # ↑
ERROR = logging.ERROR  # 40
WARNING = logging.WARNING  # 30
WARN = logging.WARN  # ↑
INFO = logging.INFO  # 20
DEBUG = logging.DEBUG  # 10
NOTSET = logging.NOTSET  # 0


def getLevelValue(level: Level) -> LevelValue:
    """
    Make a `logging` level number from more useful/intuitive things, like string
    you might get from an environment variable or command option.

    ##### Examples #####

    ##### Integers #####

    Any integer is simply returned. This follows the logic in the stdlib
    `logging` package, `logging._checkLevel` in particular.

    ```python
    >>> getLevelValue(logging.DEBUG)
    10

    >>> getLevelValue(123)
    123

    >>> getLevelValue(-1)
    -1

    ```

    No, I have no idea what kind of mess using negative level values might
    cause.

    ##### Strings #####

    Integer levels can be provided as strings. Again, they don't have to
    correspond to any named level.

    ```python
    >>> getLevelValue("8")
    8

    ```

    We also accept level *names*.

    ```python
    >>> getLevelValue("debug")
    10

    ```

    We use the oddly-named `logging.getLevelName` to figure out if a string
    is a level name (when given a string that is a level name it will
    return the integer level value).

    If we don't find the exact name we're given, we also try the upper-case
    version of the string.

    ```python
    >>> getLevelValue("DEBUG")
    10
    >>> getLevelValue("Debug")
    10

    ```

    This works with custom levels as well.

    ```python
    >>> logging.addLevelName(8, "LUCKY")
    >>> getLevelValue("lucky")
    8

    ```

    ##### Other #####

    Everything else can kick rocks:

    ```python
    >>> getLevelValue([])
    Traceback (most recent call last):
        ...
    TypeError: Expected `level` to be `int | str`, given `list`: []

    ```
    """

    if isinstance(level, int):
        return level

    if isinstance(level, str):
        if level.isdigit():
            return int(level)

        level_value = logging.getLevelName(level)

        if isinstance(level_value, int):
            return level_value

        upper_level = level.upper()

        level_value = logging.getLevelName(upper_level)

        if isinstance(level_value, int):
            return level_value

        raise TypeError(
            (
                "Neither given value {} or upper-case version {} are valid "
                "level names"
            ).format(fmt(level), fmt(upper_level))
        )

    raise TypeError(
        "Expected `level` to be `{}`, given `{}`: {}".format(
            fmt(Level), fmt(type(level)), fmt(level)
        )
    )
