import logging
import sys
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path
from typing import Optional

_LOG = logging.getLogger(__name__)

STDLIB_PATH = Path(find_spec("logging").origin).parents[1]


def is_stdlib_spec(spec: ModuleSpec) -> bool:
    if spec.origin == "built-in":
        return True

    try:
        Path(spec.origin).relative_to(STDLIB_PATH)
    except ValueError:
        return False

    return True


def get_spec(name: str) -> Optional[ModuleSpec]:
    try:
        return find_spec(name)
    except ModuleNotFoundError:
        return None


def resolve_module(name: str):
    if spec := get_spec(name):
        return (spec, name, None)
    if "." in name:
        module_name, _, attr_name = name.rpartition(".")
        if spec := get_spec(module_name):
            return (spec, module_name, attr_name)
    return None


def get_stdlib_url(module_name: str, attr_name: Optional[str]) -> str:
    return "https://docs.python.org/{}.{}/library/{}.html{}".format(
        sys.version_info[0],
        sys.version_info[1],
        module_name,
        "" if attr_name is None else f"#{module_name}.{attr_name}",
    )


def get_stdlib_md_link(name: str) -> Optional[str]:
    if resolution := resolve_module(name):
        spec, module_name, attr_name = resolution

        if is_stdlib_spec(spec):
            url = get_stdlib_url(module_name, attr_name)

            _LOG.info("  STDLIB %s", url)

            return "[{}]({})".format(name, url)

    return None
