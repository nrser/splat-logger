from io import StringIO
import logging
import json
import traceback
from typing import Type
import datetime

from rich.console import Console

from ..rich_handler import TRich, is_rich
from .json_encoder import JSONEncoder


def render_rich_to_string(rich_obj: TRich, **kwds) -> str:
    sio = StringIO()
    console = Console(file=sio, **kwds)
    console.print(rich_obj)
    return sio.getvalue()


def encode_class(cls: Type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


class JSONFormatter(logging.Formatter):
    def _format_message(self, record: logging.LogRecord) -> str:
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
            return render_rich_to_string(record.msg)

        return record.getMessage()

    def formatTime(self, record: logging.LogRecord) -> str:
        return (
            datetime.datetime.fromtimestamp(
                record.created, datetime.timezone.utc
            )
            .isoformat()
            .replace("+00:00", "Z")
        )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "name": record.name,
            "ts": self.formatTime(record),
            "msg": self._format_message(record),
        }

        if hasattr(record, "data") and record.data:
            payload["data"] = record.data

        if record.exc_info:
            exception_type, exception, tb = record.exc_info

            error = {}

            if exception_type is not None:
                error["type"] = encode_class(exception_type)

            if exception is not None:
                error["args"] = exception.args

            if tb is not None:
                error["traceback"] = traceback.format_tb(tb)

            if error:
                payload["error"] = error

        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), cls=JSONEncoder
        )
