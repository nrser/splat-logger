from contextlib import nullcontext
import logging
from typing import ContextManager

_NULL_CONTEXT = nullcontext()


def lock() -> ContextManager:
    loggingLock = getattr(logging, "_lock", None)
    if loggingLock:
        return loggingLock
    return _NULL_CONTEXT
