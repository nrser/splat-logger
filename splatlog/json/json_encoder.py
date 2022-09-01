import dataclasses
from inspect import isclass, ismethod
import json
from typing import Type, TypeVar, IO
from collections.abc import Collection, Mapping
from enum import Enum

from splatlog.lib import required_arity


def encode_class(cls: Type) -> str:
    if cls.__module__ == "builtins":
        return cls.__qualname__
    return f"{cls.__module__}.{cls.__qualname__}"


Self = TypeVar("Self", bound="JSONEncoder")


class JSONEncoder(json.JSONEncoder):
    """
    An extension of `json.JSONEncoder` that attempts to deal with all the crap
    you might splat into a log.

    ##### Usage #####

    ###### Usage with `json.dump` and `json.dumps` #######

    The encoder can be used with `json.dump` and `json.dumps` as follows.

    ```python

    >>> from sys import stdout

    >>> json.dump(dict(x=1, y=2, z=3), stdout, cls=JSONEncoder)
    {"x": 1, "y": 2, "z": 3}

    >>> json.dumps(dict(x=1, y=2, z=3), cls=JSONEncoder)
    '{"x": 1, "y": 2, "z": 3}'

    ```

    ###### Instance Usage ######

    However, usage with `json.dump` and `json.dumps` will create a new
    `splatlog.json.JSONEncoder` instance for each call. It's more efficient to
    create a single instance and use it repeatedly.

    ```python

    >>> encoder = JSONEncoder()

    ```

    The encoder provides a `splatlog.json.JSONEncoder.dump` convenience method
    for (chunked) encoding to a file-like object.

    ```python

    >>> encoder.dump(dict(x=1, y=2, z=3), stdout)
    {"x": 1, "y": 2, "z": 3}

    ```

    The inherited `json.JSONEncoder.encode` method stands-in for `json.dumps`.

    ```python

    >>> encoder.encode(dict(x=1, y=2, z=3))
    '{"x": 1, "y": 2, "z": 3}'

    ```

    ###### Construction Helpers #####

    Construction helper class methods are provided for common instance
    configurations.

    The `splatlog.json.JSONEncoder.pretty` helper creates instances that output
    "pretty" JSON by setting `splatlog.json.JSONEncoder.indent` to `4`.

    Useful for human-read output.

    ```python

    >>> pretty_encoder = JSONEncoder.pretty()
    >>> pretty_encoder.dump(dict(x=1, y=2, z=3), stdout)
    {
        "x": 1,
        "y": 2,
        "z": 3
    }

    ```

    The `splatlog.json.JSONEncoder.compact` helper creates instances that output
    the most compact JSON, limiting each output to a single line.

    Useful for machine-read output, especially log files.

    ```python

    >>> compact_encoder = JSONEncoder.compact()
    >>> compact_encoder.dump(dict(x=1, y=2, z=3), stdout)
    {"x":1,"y":2,"z":3}

    ```

    ##### Extended Encoding Capabilities #####

    The whole point of this class is to be able to encode (far) more than the
    standard `json.JSONEncoder`.

    Extended capabilities are presented in resolution order — first one that
    applies wins... or loses; if that path fails for some reason, we don't keep
    trying down-list.

    ###### Custom Handler #######

    Any object can implement a `to_json_encodable` method, and that will be used.

    ```python

    >>> class A:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_json_encodable(self):
    ...         return dict(x=self.x, y=self.y, z=self.z)

    >>> encoder.dump(A(x=1, y=2, z=3), stdout)
    {"x": 1, "y": 2, "z": 3}

    ```

    ###### Classes ######

    Classes are encoded _nominally_ as JSON strings, composed of the class
    `__module__` and `__qualname__`, joined with a `.` character.

    This is indented to keep information about the types of objects both
    specific and concise.

    ```python

    >>> class B:
    ...     pass

    >>> encoder.dump(B, stdout)
    "splatlog.json.json_encoder.B"

    ```

    For classes that are part of the top-level namespace (which have a
    `__module__` of `"builtins"`) the module part is omitted.

    Hence the top-level class `str` encodes simply as `"str"`, not as
    `"builtins.str"`.

    ```python

    >>> encoder.dump(str, stdout)
    "str"

    ```

    ###### Dataclasses ######

    Dataclass instances are encoded via `dataclasses.asdict`.

    ```python

    >>> @dataclasses.dataclass
    ... class DC:
    ...     x: int
    ...     y: int
    ...     z: int

    >>> encoder.dump(DC(x=1, y=2, z=3), stdout)
    {"x": 1, "y": 2, "z": 3}

    ```

    ###### Enums ######

    Instances of `enum.Enum` are encoded _nominally_ as JSON strings, composed
    of the class of the object (per class encoding, discussed above) and the
    object's `name`, joined (again) with a `.`.

    ```python

    >>> from enum import Enum

    >>> class Status(Enum):
    ...     OK = "ok"
    ...     ERROR = "error"

    >>> encoder.dump(Status.OK, stdout)
    "splatlog.json.json_encoder.Status.OK"

    ```

    Note that enums that descend from `enum.IntEnum` are automatically encoded
    by _value_ via the standard JSON encoder.

    ```python

    >>> from enum import IntEnum

    >>> class IntStatus(IntEnum):
    ...     OK = 200
    ...     ERROR = 500

    >>> encoder.dump(IntStatus.OK, stdout)
    200

    ```

    ###### General Conversion Methods #######

    The encoder looks for zero-arity methods named `to_dict`, `to_tuple` and
    `to_list` (in that order), and calls the first one it finds, expecting it
    to return the obvious result.

    This basically allows you to have your classes do dataclass-like encoding.

    ```python

    >>> class ToDict:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_dict(self):
    ...         return self.__dict__

    >>> encoder.dump(ToDict(1, 2, 3), stdout)
    {"x": 1, "y": 2, "z": 3}

    >>> class ToTuple:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_tuple(self):
    ...         return (self.x, self.y, self.z)

    >>> encoder.dump(ToTuple(1, 2, 3), stdout)
    [1, 2, 3]

    >>> class ToList:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_list(self):
    ...         return [self.x, self.y, self.z]

    >>> encoder.dump(ToList(1, 2, 3), stdout)
    [1, 2, 3]

    ```

    ###### Collections ######

    Objects that implement `collections.abc.Collection` are encoded as a JSON
    object containing the class and collection items.

    In the case of `collections.abc.Mapping`, items are encoded as a JSON
    object (via `dict(collection)`).

    ```python

    >>> from collections import UserDict

    >>> ud = UserDict(dict(a=1, b=2, c=3))
    >>> pretty_encoder.dump(ud, stdout)
    {
        "__class__": "collections.UserDict",
        "items": {
            "a": 1,
            "b": 2,
            "c": 3
        }
    }

    ```

    All other `collections.abc.Collection` have their items encoded as a JSON
    array (via `tuple(collection)`).

    ```python

    >>> pretty_encoder.dump({1, 2, 3}, stdout)
    {
        "__class__": "set",
        "items": [
            1,
            2,
            3
        ]
    }

    ```

    ###### Everything Else #######

    Because this encoder is focused on serializing log data that may contain any
    object, and that log data will often be examined only after said object is
    long gone, we try to provide a some-what useful catch-all.

    Anything that doesn't fall into any of the preceding categories will be
    encoded as a JSON object containing the `__class__` (as a string, per the
    _Classes_ section) and `__repr__`.

    ```python

    >>> pretty_encoder.dump(lambda x: x, stdout)
    {
        "__class__": "function",
        "__repr__": "<function <lambda> at ...>"
    }

    ```
    """

    CUSTOM_HANDLER_NAME = "to_json_encodable"

    CONVERSION_METHOD_NAMES = [
        "to_dict",
        "to_tuple",
        "to_list",
    ]

    PRETTY_KWDS = dict(indent=4)

    COMPACT_KWDS = dict(indent=None, separators=(",", ":"))

    @classmethod
    def pretty(cls, **kwds) -> Self:
        return cls(**cls.PRETTY_KWDS, **kwds)

    @classmethod
    def compact(cls, **kwds) -> Self:
        return cls(**cls.COMPACT_KWDS, **kwds)

    def default(self, obj):
        if hasattr(obj, self.__class__.CUSTOM_HANDLER_NAME):
            attr = getattr(obj, self.__class__.CUSTOM_HANDLER_NAME)
            if ismethod(attr) and required_arity(attr) == 0:
                return attr()

        if isclass(obj):
            return encode_class(obj)

        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)

        if isinstance(obj, Enum):
            return f"{encode_class(obj.__class__)}.{obj.name}"

        for method_name in self.__class__.CONVERSION_METHOD_NAMES:
            if hasattr(obj, method_name):
                attr = getattr(obj, method_name)
                if ismethod(attr) and required_arity(attr) == 0:
                    return attr()

        if isinstance(obj, Mapping):
            return {
                "__class__": encode_class(obj.__class__),
                "items": dict(obj),
            }

        if isinstance(obj, Collection):
            return {
                "__class__": encode_class(obj.__class__),
                "items": tuple(obj),
            }

        return {
            "__class__": encode_class(obj.__class__),
            "__repr__": repr(obj),
        }

    def dump(self, obj, fp: IO) -> None:
        for chunk in self.iterencode(obj):
            fp.write(chunk)
