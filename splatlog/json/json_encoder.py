import dataclasses
from inspect import isclass, ismethod
import json
from typing import Type
from collections.abc import Collection, Mapping
from enum import Enum


def encode_class(cls: Type) -> str:
    if cls.__module__ == "builtins":
        return cls.__qualname__
    return f"{cls.__module__}.{cls.__qualname__}"


class JSONEncoder(json.JSONEncoder):
    """
    ##### Examples #####

    ###### Classes ######

    Classes are encoded _nominally_ as JSON strings, composed of the class
    `__module__` and `__qualname__`, joined with a `.` character.

    This is indented to keep information about the types of objects both
    specific and concise.

    ```python

    >>> from sys import stdout

    >>> class A:
    ...     pass

    >>> json.dump(A, stdout, cls=JSONEncoder, indent=4)
    "splatlog.json.json_encoder.A"

    ```

    For classes that are part of the top-level namespace (which have a
    `__module__` of `"builtins"`) the module part is omitted.

    Hence the top-level class `str` encodes simply as `"str"`, not as
    `"builtins.str"`.

    ```python

    >>> json.dump(str, stdout, cls=JSONEncoder, indent=4)
    "str"

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

    """

    def default(self, obj):
        if isclass(obj):
            return encode_class(obj)

        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)

        if isinstance(obj, Enum):
            return f"{encode_class(obj.__class__)}.{obj.name}"

        if hasattr(obj, "to_dict"):
            to_dict = getattr(obj, "to_dict")
            if ismethod(to_dict):
                return to_dict()

        if hasattr(obj, "to_tuple"):
            to_tuple = getattr(obj, "to_tuple")
            if ismethod(to_tuple):
                return to_tuple()

        if hasattr(obj, "to_list"):
            to_list = getattr(obj, "to_list")
            if ismethod(to_list):
                return to_list()

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
