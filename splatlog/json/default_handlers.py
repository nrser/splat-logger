import dataclasses
from collections.abc import Callable, Mapping, Collection
from enum import Enum
from inspect import isclass
from typing import Any, Type

from splatlog.lib import full_class_name, has_method

from .json_typings import JSONEncodable

THandleFn = Callable[[Any], JSONEncodable]


@dataclasses.dataclass(frozen=True, order=True)
class DefaultHandler:
    priority: int
    name: str
    is_match: Callable[[Any], bool]
    handle: THandleFn


def instance_handler(
    cls: Type, priority: int, handle: THandleFn
) -> DefaultHandler:
    return DefaultHandler(
        name=full_class_name(cls),
        priority=priority,
        is_match=lambda obj: isinstance(obj, cls),
        handle=handle,
    )


def method_handler(method_name: str, priority: int) -> DefaultHandler:
    return DefaultHandler(
        name=f".{method_name}()",
        priority=priority,
        is_match=lambda obj: has_method(obj, method_name, req_arity=0),
        handle=lambda obj: getattr(obj, method_name)(),
    )


TO_JSON_ENCODABLE_HANDLER = method_handler(
    method_name="to_json_encodable",
    priority=10,
)

CLASS_HANDLER = DefaultHandler(
    name="class",
    priority=20,
    is_match=isclass,
    handle=full_class_name,
)

DATACLASS_HANDLER = DefaultHandler(
    name="dataclasses.dataclass",
    priority=30,
    is_match=dataclasses.is_dataclass,
    handle=dataclasses.asdict,
)

ENUM_HANDLER = instance_handler(
    cls=Enum,
    priority=40,
    handle=lambda obj: f"{full_class_name(obj.__class__)}.{obj.name}",
)

TO_DICT_HANDLER = method_handler(method_name="to_dict", priority=42)
TO_TUPLE_HANDLER = method_handler(method_name="to_tuple", priority=45)
TO_LIST_HANDLER = method_handler(method_name="to_list", priority=48)

MAPPING_HANDLER = instance_handler(
    cls=Mapping,
    priority=50,
    handle=lambda obj: {
        "__class__": full_class_name(obj.__class__),
        "items": dict(obj),
    },
)

COLLECTION_HANDLER = instance_handler(
    cls=Collection,
    priority=60,
    handle=lambda obj: {
        "__class__": full_class_name(obj.__class__),
        "items": tuple(obj),
    },
)

FALLBACK_HANDLER = DefaultHandler(
    name="fallback",
    priority=100,
    is_match=lambda obj: True,
    handle=lambda obj: {
        "__class__": full_class_name(obj.__class__),
        "__repr__": repr(obj),
    },
)

ALL_HANDLERS = tuple(
    sorted(x for x in locals().values() if isinstance(x, DefaultHandler))
)
