from __future__ import annotations
from threading import RLock
from types import GenericAlias
from typing import Callable, Generic, TypeVar, overload, Any


_NOT_FOUND = object()


TValue = TypeVar("TValue")


class SlotCachedProperty(Generic[TValue]):
    """
    This is basically just an adaptation of `functools.cached_property` that
    works with types that use `__slots__`.

    If you have a property named `blah` you must have a slot named `_blah` for
    it to go in.
    """

    def __init__(self, func: Callable[[Any], TValue]):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
        self.lock = RLock()

    def __set_name__(self, owner, name):
        attrname = "_" + name
        if self.attrname is None:
            self.attrname = attrname
        elif attrname != self.attrname:
            raise TypeError(
                f"Cannot assign the same {self.__class__.__name__} to two "
                f"different names ({self.attrname!r} and {attrname!r})"
            )

    @overload
    def __get__(
        self, instance: None, owner: None
    ) -> SlotCachedProperty[TValue]:
        ...

    @overload
    def __get__(self, instance: Any, owner: type) -> TValue:
        ...

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                f"Cannot use {self.__class__.__name__} instance without "
                "calling __set_name__ on it."
            )
        val = getattr(instance, self.attrname, _NOT_FOUND)
        if val is _NOT_FOUND:
            with self.lock:
                # check if another thread filled cache while we awaited lock
                val = getattr(instance, self.attrname, _NOT_FOUND)
                if val is _NOT_FOUND:
                    val = self.func(instance)
                    setattr(self, self.attrname, val)
        return val

    __class_getitem__ = classmethod(GenericAlias)
