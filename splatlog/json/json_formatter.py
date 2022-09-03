from io import StringIO
import logging
import json
import traceback
from typing import Optional
import datetime

from rich.console import Console

from splatlog.lib import full_class_name
from splatlog.rich_handler import TRich, is_rich

from .json_encoder import JSONEncoder

_DEFAULT_ENCODER = JSONEncoder.compact()


def render_rich_to_string(rich_obj: TRich, **kwds) -> str:
    sio = StringIO()
    console = Console(file=sio, **kwds)
    console.print(rich_obj)
    return sio.getvalue()


class JSONFormatter(logging.Formatter):
    _encoder: json.JSONEncoder

    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style="%",
        validate=True,
        *,
        defaults=None,
        encoder: Optional[json.JSONEncoder] = None,
    ):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

        if encoder is None:
            self._encoder = _DEFAULT_ENCODER
        else:
            self._encoder = encoder

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
            "ts": self.formatTime(record),
            "lvl": record.levelname,
            "log": record.name,
            "msg": self._format_message(record),
        }

        if hasattr(record, "data") and record.data:
            payload["data"] = record.data

        if record.exc_info:
            exception_type, exception, tb = record.exc_info

            error = {}

            if exception_type is not None:
                error["type"] = full_class_name(exception_type)

            if exception is not None:
                error["args"] = exception.args

            if tb is not None:
                error["tb"] = traceback.format_tb(tb)

            if error:
                payload["error"] = error

        return self._encoder.encode(payload)
