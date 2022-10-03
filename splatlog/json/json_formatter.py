import logging
import json
from typing import Any, Optional, Union
from datetime import datetime, timezone

from splatlog.lib import is_rich, capture_riches
from splatlog.typings import ExcInfo

from .json_encoder import JSONEncoder

_DEFAULT_ENCODER = JSONEncoder.compact()

LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo


def _make_log_record(
    name: str = __name__,
    level: int = logging.INFO,
    pathname: str = __file__,
    lineno: int = 123,
    msg: str = "Test message",
    args: Union[tuple, dict[str, Any]] = (),
    exc_info: Optional[ExcInfo] = None,
    func: Optional[str] = None,
    sinfo: Optional[str] = None,
    *,
    created: Union[None, float, datetime] = None,
    data: Optional[dict[str, Any]] = None,
) -> logging.LogRecord:
    """
    Used in testing to make `logging.LogRecord` instances. Provides defaults
    for all of the parameters, since you often only care about setting some
    subset.

    Provides a hack to set the `logging.LogRecord.created` attribute (as well as
    associated `logging.LogRecord.msecs` and `logging.LogRecord.relativeCreated`
    attributes) by providing an extra `created` keyword parameter.

    Also provides a way to set the `data` attribute by passing the extra `data`
    keyword parameter.

    SEE https://docs.python.org/3.10/library/logging.html#logging.LogRecord
    """
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname=pathname,
        lineno=lineno,
        msg=msg,
        args=args,
        exc_info=exc_info,
        func=func,
        sinfo=sinfo,
    )

    if created is not None:
        if isinstance(created, datetime):
            created = created.timestamp()
        record.created = created
        record.msecs = (created - int(created)) * 1000
        record.relativeCreated = (created - logging._startTime) * 1000

    if data is not None:
        setattr(record, "data", data)

    return record


class JSONFormatter(logging.Formatter):
    _encoder: json.JSONEncoder
    _tz: Optional[timezone]
    _use_Z_for_utc: bool

    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style="%",
        validate=True,
        *,
        defaults=None,
        encoder: Optional[json.JSONEncoder] = None,
        tz: Optional[timezone] = LOCAL_TIMEZONE,
        use_Z_for_utc: bool = True,
    ):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

        self._encoder = _DEFAULT_ENCODER if encoder is None else encoder
        self._tz = tz
        self._use_Z_for_utc = use_Z_for_utc

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
            return capture_riches(record.msg)

        return record.getMessage()

    def _format_timestamp(self, record: logging.LogRecord) -> str:
        """
        ##### Examples #####

        Using UTC timestamps.

        ```python
        >>> r_1 = _make_log_record(
        ...     created=datetime(
        ...         2022, 9, 4, 3, 4, 5, 123456, tzinfo=timezone.utc
        ...     )
        ... )

        >>> JSONFormatter(tz=timezone.utc)._format_timestamp(r_1)
        '2022-09-04T03:04:05.123456Z'

        ```

        Using the `+00:00` suffix (instead of the default `Z`) for UTC.

        ```python

        >>> JSONFormatter(
        ...     tz=timezone.utc,
        ...     use_Z_for_utc=False
        ... )._format_timestamp(r_1)
        '2022-09-04T03:04:05.123456+00:00'

        ```

        Using a specific timezone. The default behavior is to use the machine's
        local timezone, stored in `LOCAL_TIMEZONE`, but that's tricky to test,
        and this showcases the same functionality.

        ```python

        >>> from zoneinfo import ZoneInfo

        >>> la_tz = ZoneInfo("America/Los_Angeles")
        >>> la_formatter = JSONFormatter(tz=la_tz)

        >>> r_2 = _make_log_record(
        ...     created=datetime(2022, 9, 4, 3, 4, 5, 123456, tzinfo=la_tz)
        ... )
        >>> la_formatter._format_timestamp(r_2)
        '2022-09-04T03:04:05.123456-07:00'

        ```
        """
        formatted = datetime.fromtimestamp(
            record.created, tz=self._tz
        ).isoformat()

        if self._use_Z_for_utc and formatted.endswith("+00:00"):
            return formatted.replace("+00:00", "Z")

        return formatted

    def format(self, record: logging.LogRecord) -> str:
        """
        ##### Examples #####

        Basic example.

        ```python

        >>> r_1 = _make_log_record(
        ...     created=datetime(
        ...         2022, 9, 4, 3, 4, 5, 123456, tzinfo=timezone.utc
        ...     )
        ... )

        >>> formatter = JSONFormatter(
        ...     encoder=JSONEncoder.pretty(),
        ...     tz=timezone.utc,
        ... )

        >>> print(formatter.format(r_1))
        {
            "t": "2022-09-04T03:04:05.123456Z",
            "level": "INFO",
            "name": "splatlog.json.json_formatter",
            "file": ".../splatlog/json/json_formatter.py",
            "line": 123,
            "msg": "Test message"
        }

        ```

        With some `data` attached.

        ```python

        >>> r_2 = _make_log_record(
        ...     created=datetime(
        ...         2022, 9, 4, 3, 4, 5, 123456, tzinfo=timezone.utc
        ...     ),
        ...     data=dict(
        ...         x=1,
        ...         y=2,
        ...     )
        ... )

        >>> print(formatter.format(r_2))
        {
            "t": "2022-09-04T03:04:05.123456Z",
            "level": "INFO",
            "name": "splatlog.json.json_formatter",
            "file": ".../splatlog/json/json_formatter.py",
            "line": 123,
            "msg": "Test message",
            "data": {
                "x": 1,
                "y": 2
            }
        }

        ```

        With error information (`exc_info`).

        ```python
        >>> import sys

        >>> try:
        ...     raise RuntimeError("Something went wrong")
        ... except:
        ...     r_3 = _make_log_record(
        ...         created=datetime(
        ...             2022, 9, 4, 3, 4, 5, 123456, tzinfo=timezone.utc
        ...         ),
        ...         exc_info=sys.exc_info(),
        ...     )
        ...     print(formatter.format(r_3))
        {
            "t": "2022-09-04T03:04:05.123456Z",
            "level": "INFO",
            "name": "splatlog.json.json_formatter",
            "file": ".../splatlog/json/json_formatter.py",
            "line": 123,
            "msg": "Test message",
            "error": {
                "type": "RuntimeError",
                "msg": "Something went wrong",
                "traceback": [
                    {
                        "file": "<doctest ...>",
                        "line": 2,
                        "name": "<module>",
                        "text": "raise RuntimeError(\\"Something went wrong\\")"
                    }
                ]
            }
        }

        ```

        """
        payload = {
            "t": self._format_timestamp(record),
            "level": record.levelname,
            "name": record.name,
            "file": record.pathname,
            "line": record.lineno,
            "msg": self._format_message(record),
        }

        if hasattr(record, "data") and record.data:
            payload["data"] = record.data

        if record.exc_info is not None:
            payload["error"] = record.exc_info[1]

        return self._encoder.encode(payload)
