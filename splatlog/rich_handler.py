"""\
Contains the `RichHandler` class.
"""

from __future__ import annotations
from typing import IO, Any, Optional, Union
import logging
import sys
from collections.abc import Mapping

from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.theme import Theme
from rich.traceback import Traceback

from splatlog.lib import TRich, is_rich, ntv_table, THEME


class RichHandler(logging.Handler):
    """\
    A `logging.Handler` extension that uses [rich][] to print pretty nice log
    entries to the console.

    Output is meant for specifically humans.
    """

    DEFAULT_THEME = THEME

    # By default, all logging levels log to the `err` console
    DEFAULT_LEVEL_MAP = {
        logging.CRITICAL: "err",
        logging.ERROR: "err",
        logging.WARNING: "err",
        logging.INFO: "err",
        logging.DEBUG: "err",
    }

    @classmethod
    def default(cls) -> RichHandler:
        instance = getattr(cls, "__default", None)
        if instance is not None and instance.__class__ == cls:
            return instance
        instance = cls()
        setattr(cls, "__default", instance)
        return instance

    consoles: Mapping[str, Console]
    level_map: Mapping[int, str]

    def __init__(
        self,
        level: int = logging.NOTSET,
        *,
        consoles: Optional[Mapping[str, Console]] = None,
        level_map: Optional[Mapping[int, str]] = None,
        theme: Union[None, Theme, IO[str], str] = None,
    ):
        super().__init__(level=level)

        if theme is None:
            # If no theme was provided create an instance-owned copy of the
            # default theme (so that any modifications don't spread to any other
            # instances... which usually doesn't matter, since there is
            # typically only one instance, but it's good practice I guess).
            self.theme = Theme(self.DEFAULT_THEME.styles)
        elif isinstance(theme, Theme):
            # Given a `rich.theme.Theme`, which can be used directly
            self.theme = theme
        elif isinstance(theme, IO):
            # Given an open file to read the theme from
            self.theme = Theme.from_file(theme)
        elif isinstance(theme, str):
            # Given a string, which is understood as a config file path to read
            # the theme from
            self.theme = Theme.read(theme)
        else:
            raise TypeError(
                "`theme` arg must be `rich.theme.Theme`, `typing.IO` or "
                + f"`str, given {type(theme)}: {theme!r}"
            )

        if consoles is None:
            # If no console mapping was provided, create a minimal mapping of
            # default consoles:
            #
            # -   "out" -> `sys.stdout`
            # -   "err" -> `sys.stderr`
            #
            # using the `theme` resolved above.
            self.consoles = {
                "out": Console(file=sys.stdout, theme=self.theme),
                "err": Console(file=sys.stderr, theme=self.theme),
            }
        else:
            # If we were provided a console mapping, convert it into an
            # instance-owned mutable `dict`
            self.consoles = {**consoles}

            # Ensure we have at least the standard "out" and "err" mappings
            # available
            if "out" not in self.consoles:
                self.consoles["out"] = Console(file=sys.stdout, theme=theme)
            if "err" not in self.consoles:
                self.consoles["err"] = Console(file=sys.stderr, theme=theme)

        if level_map is None:
            # No level map given; use an instance-owned copy of the default
            # level map
            self.level_map = self.DEFAULT_LEVEL_MAP.copy()
        else:
            # Given a level map -- overlay it on top of the default one in an
            # instance-owned `dict`
            self.level_map = {**self.DEFAULT_LEVEL_MAP, **level_map}

    def emit(self, record):
        # pylint: disable=broad-except
        try:
            self._emit_table(record)
        except (KeyboardInterrupt, SystemExit) as error:
            # We want these guys to bub' up
            raise error
        except Exception as error:
            self.consoles["err"].print_exception()
            # self.handleError(record)

    def _get_rich_msg(self, record) -> TRich:
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
        return Text(msg, style="log.message")

    def _emit_table(self, record):
        # SEE   https://github.com/willmcgugan/rich/blob/25a1bf06b4854bd8d9239f8ba05678d2c60a62ad/rich/_log_render.py#L26

        console = self.consoles.get(
            self.level_map.get(record.levelno, "err"),
            self.consoles["err"],
        )

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
