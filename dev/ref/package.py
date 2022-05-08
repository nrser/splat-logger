from __future__ import annotations
import logging
from typing import Dict

from splatlog.typings import TLevelValue


class Package:
    _INSTANCES: Dict[str, Package] = {}

    @classmethod
    def upsert(
        cls,
        module_name: str,
        level: TLevelValue,
        console_handler: logging.Handler,
    ) -> Package:
        if module_name in Package._INSTANCES:
            # package = Package.
            Package._INSTANCES[module_name].update(level, console_handler)
        else:
            cls.insert()

    module_name: str
    console_handler: logging.Handler
