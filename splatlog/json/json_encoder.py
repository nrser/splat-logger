import dataclasses
from inspect import isclass, ismethod
import json
from typing import Type
from collections.abc import Collection, Mapping
from enum import Enum

from splatlog.lib import required_arity


def encode_class(cls: Type) -> str:
    if cls.__module__ == "builtins":
        return cls.__qualname__
    return f"{cls.__module__}.{cls.__qualname__}"


class JSONEncoder(json.JSONEncoder):
    """
    An extension of `json.JSONEncoder` that attempts to deal with all the crap
    you might splat into a log.

    ##### Examples #####

    Presented in resolution order — first one that applies wins... or loses; if
    that path fails for some reason, we don't keep trying down-list.

    ###### Specific Handler #######

    Any object can implement a `to_json_default` method, and that will be used.

    ```python

    >>> class A:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_json_default(self):
    ...         return dict(x=self.x, y=self.y, z=self.z)

    >>> json.dump(A(x=1, y=2, z=3), stdout, cls=JSONEncoder, indent=4)
    {
        "x": 1,
        "y": 2,
        "z": 3
    }

    ```

    ###### Classes ######

    Classes are encoded _nominally_ as JSON strings, composed of the class
    `__module__` and `__qualname__`, joined with a `.` character.

    This is indented to keep information about the types of objects both
    specific and concise.

    ```python

    >>> from sys import stdout

    >>> class B:
    ...     pass

    >>> json.dump(B, stdout, cls=JSONEncoder, indent=4)
    "splatlog.json.json_encoder.B"

    ```

    For classes that are part of the top-level namespace (which have a
    `__module__` of `"builtins"`) the module part is omitted.

    Hence the top-level class `str` encodes simply as `"str"`, not as
    `"builtins.str"`.

    ```python

    >>> json.dump(str, stdout, cls=JSONEncoder, indent=4)
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

    >>> json.dump(DC(x=1, y=2, z=3), stdout, cls=JSONEncoder, indent=4)
    {
        "x": 1,
        "y": 2,
        "z": 3
    }

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

    >>> json.dump(Status.OK, stdout, cls=JSONEncoder, indent=4)
    "splatlog.json.json_encoder.Status.OK"

    ```

    Note that enums that descend from `enum.IntEnum` are automatically encoded
    by _value_ via the standard JSON encoder.

    ```python

    >>> from enum import IntEnum

    >>> class IntStatus(IntEnum):
    ...     OK = 200
    ...     ERROR = 500

    >>> json.dump(IntStatus.OK, stdout, cls=JSONEncoder, indent=4)
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

    >>> json.dump(ToDict(1, 2, 3), stdout, cls=JSONEncoder)
    {"x": 1, "y": 2, "z": 3}

    >>> class ToTuple:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_tuple(self):
    ...         return (self.x, self.y, self.z)

    >>> json.dump(ToTuple(1, 2, 3), stdout, cls=JSONEncoder)
    [1, 2, 3]

    >>> class ToList:
    ...     def __init__(self, x, y, z):
    ...         self.x = x
    ...         self.y = y
    ...         self.z = z
    ...
    ...     def to_list(self):
    ...         return [self.x, self.y, self.z]

    >>> json.dump(ToList(1, 2, 3), stdout, cls=JSONEncoder)
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
    >>> json.dump(ud, stdout, cls=JSONEncoder, indent=4)
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

    >>> json.dump({1, 2, 3}, stdout, cls=JSONEncoder, indent=4)
    {
        "__class__": "set",
        "items": [
            1,
            2,
            3
        ]
    }

    ```
    """

    CONVERSION_METHOD_NAMES = [
        "to_dict",
        "to_tuple",
        "to_list",
    ]

    def default(self, obj):
        if hasattr(obj, "to_json_default"):
            attr = getattr(obj, "to_json_default")
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
