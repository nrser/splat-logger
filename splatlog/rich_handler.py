"""\
Contains the `RichHandler` class.
"""

from __future__ import annotations
from typing import IO, Any, Callable, Literal, Optional, Union
import logging
import sys

from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback

from splatlog.lib import TRich, is_rich, ntv_table, THEME, fmt
from splatlog.lib.typeguard import satisfies
from splatlog.splat_handler import SplatHandler
from splatlog.typings import Level, LevelValue
from splatlog.verbosity import VerbosityLevelsMap

StdioName = Literal["stdout", "stderr"]
ConsoleSelector = Callable[[LevelValue], Console]
ConsoleCastable = Union[None, Console, StdioName, IO[str], ConsoleSelector]
ThemeCastable = Union[None, Theme, IO[str]]


class RichHandler(SplatHandler):
    """\
    A `logging.Handler` extension that uses [rich][] to print pretty nice log
    entries to the console.

    Output is meant for specifically humans.
    """

    DEFAULT_THEME = THEME

    @classmethod
    def castTheme(cls, theme: object) -> Theme:
        if theme is None:
            # If no theme was provided create an instance-owned copy of the
            # default theme (so that any modifications don't spread to any other
            # instances... which usually doesn't matter, since there is
            # typically only one instance, but it's good practice I guess).
            return Theme(cls.DEFAULT_THEME.styles)

        if isinstance(theme, Theme):
            # Given a `rich.theme.Theme`, which can be used directly
            return theme

        if satisfies(theme, IO[str]):
            # Given an open file to read the theme from
            return Theme.from_file(theme)

        raise TypeError(
            "Expected `theme` to be {}, given {}: {}".format(
                fmt(Union[None, Theme, IO[str]]), fmt(type(theme)), fmt(theme)
            )
        )

    @classmethod
    def castConsole(
        cls, console: ConsoleCastable, theme: Theme
    ) -> Union[Console, ConsoleSelector]:
        if console is None:
            return Console(sys.stderr, theme=theme)

        if isinstance(console, Console):
            return console

        if satisfies(console, StdioName):
            return Console(
                file=(sys.stderr if console == "stderr" else sys.stdout),
                theme=theme,
            )

        if satisfies(console, IO[str]):
            return Console(file=console, theme=theme)

        if satisfies(console, ConsoleSelector):
            return console

        raise TypeError(
            "Expected `console` to be {}, given {}: {}".format(
                fmt(Union[Console, StdioName, IO[str], ConsoleSelector]),
                fmt(type(console)),
                fmt(console),
            )
        )

    @classmethod
    def default(cls) -> RichHandler:
        instance = getattr(cls, "__default", None)
        if instance is not None and instance.__class__ == cls:
            return instance
        instance = cls()
        setattr(cls, "__default", instance)
        return instance

    console: Union[Console, ConsoleSelector]

    def __init__(
        self,
        level: Level = logging.NOTSET,
        *,
        console: ConsoleCastable = None,
        theme: ThemeCastable = None,
        verbosityLevels: Optional[VerbosityLevelsMap] = None,
    ):
        super().__init__(level=level, verbosityLevels=verbosityLevels)

        self.theme = self.__class__.castTheme(theme)
        self.console = self.__class__.castConsole(console, self.theme)

    def resolveConsole(self, levelValue: LevelValue) -> Console:
        if isinstance(self.console, Console):
            return self.console
        return self.console(levelValue)

    def emit(self, record):
        # pylint: disable=broad-except
        try:
            self._emit_table(record)
        except (RecursionError, KeyboardInterrupt, SystemExit):
            # RecursionError from cPython, they cite issue 36272; the other ones
            # we want to bubble up in interactive shells
            raise
        except Exception:
            # Just use the damn built-in one, it shouldn't happen much really
            #
            # NOTE  I _used_ to have this, and I replaced it with a
            #       `Console.print_exception()` call... probably because it
            #       sucked... but after looking at `logging.Handler.handleError`
            #       I realize it's more complicated to do correctly. Maybe it
            #       will end up being worth the effort and I'll come back to it.
            #
            self.handleError(record)

    def _get_rich_msg(self, record: logging.LogRecord) -> TRich:
        # Get a "rich" version of `record.msg` to render
        #
        # NOTE  `str` instances can be rendered by Rich, but they do no count as
        #       "rich" -- i.e. `is_rich(str) -> False`.
        if is_rich(record.msg):
            # A rich message was provided, just use that.
            #
            # NOTE  In this case, any interpolation `args` assigned to the
            #       `record` are silently ignored because I'm not sure what we
            #       would do with them.
            return record.msg

        # `record.msg` is _not_ a Rich renderable; it is treated like a
        # string (like logging normally work).
        #
        # Make sure we actually have a string:
        msg = record.msg if isinstance(record.msg, str) else str(record.msg)

        # See if there are `record.args` to interpolate.
        if record.args:
            # There are; they are %-formatted into the `str` representation
            # of `record.msg`, keeping with the "standard" logging behavior.
            msg = msg % record.args

        # Results are wrapped in a `rich.text.Text` for render, which is
        # assigned the `log.message` style (though that style is empty by
        # default).
        return Text.from_markup(msg, style="log.message")

    def _emit_table(self, record):
        # SEE   https://github.com/willmcgugan/rich/blob/25a1bf06b4854bd8d9239f8ba05678d2c60a62ad/rich/_log_render.py#L26

        console = self.resolveConsole(record.levelno)

        output = Table.grid(padding=(0, 1))
        output.expand = True

        # Left column -- log level, time
        output.add_column(width=8)

        # Main column -- log name, message, args
        output.add_column(ratio=1, overflow="fold")

        output.add_row(
            Text(
                record.levelname,
                style=f"logging.level.{record.levelname.lower()}",
            ),
            Text(record.name, style="log.name"),
        )

        output.add_row(
            Text("msg", style="log.label"), self._get_rich_msg(record)
        )

        if hasattr(record, "data") and record.data:
            output.add_row(
                Text("data", style="log.label"), ntv_table(record.data)
            )

        if record.exc_info:
            output.add_row(
                Text("err", style="log.label"),
                Traceback.from_exception(*record.exc_info),
            )

        console.print(output)
