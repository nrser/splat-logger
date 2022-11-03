from contextlib import nullcontext
import logging
from typing import ContextManager

_NULL_CONTEXT = nullcontext()


def lock() -> ContextManager:
    logging_lock = getattr(logging, "_lock", None)
    if logging_lock:
        return logging_lock
    return _NULL_CONTEXT
