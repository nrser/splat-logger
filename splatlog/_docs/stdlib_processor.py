from dataclasses import dataclass
from functools import cached_property
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
import logging
from pathlib import Path
import re
import sys
from typing import Optional, TypeGuard

from novella.markdown.preprocessor import MarkdownPreprocessor, MarkdownFiles
from novella.markdown.tagparser import Tag, parse_inline_tags, replace_tags
from pydoc_markdown.interfaces import Processor, Resolver, ResolverV2
from pydoc_markdown.util.docspec import ApiSuite
from pydoc_markdown.contrib.processors.crossref import CrossrefProcessor
from docspec import ApiObject

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


class StdlibProcessor(MarkdownPreprocessor):
    def setup(self) -> None:
        if self.dependencies is None and self.predecessors is None:
            self.precedes("pydoc")

    def process_files(self, files: MarkdownFiles) -> None:
        for file in files:
            tags = [
                t for t in parse_inline_tags(file.content) if t.name == "pylink"
            ]
            file.content = replace_tags(
                file.content, tags, lambda t: self._replace_tag(t)
            )

    def _replace_tag(self, tag: Tag) -> str | None:
        content = tag.args.strip()
        if resolution := resolve_module(content):
            spec, module_name, attr_name = resolution

            if not is_stdlib_spec(spec):
                return None

            return "[{}]({})".format(
                content, get_stdlib_url(module_name, attr_name)
            )


class MyProcessor(CrossrefProcessor):
    def _preprocess_refs(
        self,
        node: ApiObject,
        resolver: Optional[Resolver],
        suite: ApiSuite,
        unresolved: dict[str, list[str]],
    ) -> None:
        if not node.docstring:
            return

        def handler(match: re.Match) -> str:
            name = match.group(1)

            if self.resolver_v2:
                target = self.resolver_v2.resolve_reference(suite, node, name)
                if target:
                    return f'{{@link pydoc:{".".join(x.name for x in target.path)}}}'

            elif resolver:
                href = resolver.resolve_ref(node, name)
                if href:
                    return "[`{}`]({})".format(name, href)

            if resolution := resolve_module(name):
                spec, module_name, attr_name = resolution

                if is_stdlib_spec(spec):
                    return "[{}]({})".format(
                        name, get_stdlib_url(module_name, attr_name)
                    )

            return match.group(0)

        node.docstring.content = re.sub(
            r"\B`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`",
            handler,
            node.docstring.content,
        )
