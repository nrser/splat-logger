import logging
from typing import TypeGuard

from splatlog.lib.text import fmt
from splatlog.typings import Level, LevelName, LevelValue

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


def get_level_value(level: Level) -> LevelValue:
    """
    Make a `logging` level number from more useful/intuitive things, like string
    you might get from an environment variable or command option.

    ##### Examples #####

    ##### Integers #####

    Any integer is simply returned. This follows the logic in the stdlib
    `logging` package, `logging._checkLevel` in particular.

    ```python
    >>> get_level_value(logging.DEBUG)
    10

    >>> get_level_value(123)
    123

    >>> get_level_value(-1)
    -1

    ```

    No, I have no idea what kind of mess using negative level values might
    cause.

    ##### Strings #####

    Integer levels can be provided as strings. Again, they don't have to
    correspond to any named level.

    ```python
    >>> get_level_value("8")
    8

    ```

    We also accept level *names*.

    ```python
    >>> get_level_value("debug")
    10

    ```

    We use the oddly-named `logging.getLevelName` to figure out if a string
    is a level name (when given a string that is a level name it will
    return the integer level value).

    If we don't find the exact name we're given, we also try the upper-case
    version of the string.

    ```python
    >>> get_level_value("DEBUG")
    10
    >>> get_level_value("Debug")
    10

    ```

    This works with custom levels as well.

    ```python
    >>> logging.addLevelName(8, "LUCKY")
    >>> get_level_value("lucky")
    8

    ```

    ##### Other #####

    Everything else can kick rocks:

    ```python
    >>> get_level_value([])
    Traceback (most recent call last):
        ...
    TypeError: Expected `level` to be `int | str`, given `list`: []

    ```
    """

    if isinstance(level, int):
        # TODO Make consistent with `is_level_value`?
        #
        # if is_level_value(level):
        #     return level

        # raise TypeError(f"`int` {level!r} is not a named log level")

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


def is_level_name(name: object) -> TypeGuard[LevelName]:
    """
    ##### Examples #####

    ```python
    >>> is_level_name("DEBUG")
    True

    >>> is_level_name("LEVEL_NAME_TEST")
    False

    >>> level_value = hash("LEVEL_NAME_TEST") # Use somewhat unique int
    >>> logging.addLevelName(level_value, "LEVEL_NAME_TEST")
    >>> is_level_name("LEVEL_NAME_TEST")
    True

    ```
    """
    return isinstance(name, str) and isinstance(logging.getLevelName(name), int)


def is_level_value(value: object) -> TypeGuard[LevelValue]:
    """
    Test if `value` is a level value.

    Specifically, tests if `value` is a _named_ level value — a builtin one
    like `logging.DEBUG` or a custom one added with `logging.addLevelName`.

    Technically, it seems like you can use _any_ `int` as a level value, but it
    seems like it makes things simpler if all `LevelValue` have `LevelName` and
    vice-versa.

    ##### Examples #####

    ```python
    >>> is_level_value(logging.DEBUG)
    True

    >>> level_value = hash("LEVEL_VALUE_TEST") # Use somewhat unique int
    >>> is_level_value(level_value)
    False

    >>> logging.addLevelName(level_value, "LEVEL_VALUE_TEST")
    >>> is_level_value(level_value)
    True

    ```
    """
    return (
        isinstance(value, int)
        and logging.getLevelName(value) != f"Level {value}"
    )


def is_level(level: object) -> TypeGuard[Level]:
    return is_level_name(level) or is_level_value(level)
