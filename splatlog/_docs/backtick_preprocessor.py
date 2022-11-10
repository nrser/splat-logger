from dataclasses import dataclass
from functools import cached_property
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from io import StringIO
import logging
from pathlib import Path
import re
import sys
from typing import Callable, Iterable, Optional, Sequence, TypeGuard, TypeVar

from novella.markdown.preprocessor import (
    MarkdownPreprocessor,
    MarkdownFiles,
    MarkdownFile,
)
from novella.markdown.tagparser import Tag, parse_inline_tags, replace_tags
from pydoc_markdown.interfaces import Processor, Resolver, ResolverV2
from pydoc_markdown.util.docspec import ApiSuite
from pydoc_markdown.contrib.processors.crossref import CrossrefProcessor
from pydoc_markdown.novella.preprocessor import PydocTagPreprocessor
from docspec import ApiObject
from pydoc_markdown.contrib.renderers.markdown import MarkdownReferenceResolver

from splatlog._docs.backtick_src_processor import BacktickSrcProcessor


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


def resolve_stdlib_module(name: str):
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


T = TypeVar("T")


def index_where(iterable: Iterable[T], predicate: Callable[[T], bool]) -> int:
    for index, entry in enumerate(iterable):
        if predicate(entry):
            return index

    raise ValueError("no match")


def insert_before(
    list_: list[T], value: T, predicate: Callable[[T], bool]
) -> list[T]:
    """
    ##### Examples #####

    ```python
    >>> insert_before([1, 2, 3], 888, lambda n: n == 2)
    [1, 888, 2, 3]

    ```
    """
    list_.insert(index_where(list_, predicate), value)
    return list_


class BacktickPreprocessor(PydocTagPreprocessor):
    """Hey"""

    def __post_init__(self) -> None:
        super().__post_init__()

        insert_before(
            self._processors,
            BacktickSrcProcessor(
                resolver_v2=MarkdownReferenceResolver(global_=True)
            ),
            lambda proc: isinstance(proc, CrossrefProcessor),
        )

        # xref_proc_index = index_where(
        #     self._processors, lambda proc: isinstance(proc, CrossrefProcessor)
        # )

        # self._processors[xref_proc_index] = BacktickSrcProcessor(
        #     resolver_v2=MarkdownReferenceResolver(global_=True)
        # )

        # self._processors.append(
        #     BacktickSrcProcessor(
        #         resolver_v2=MarkdownReferenceResolver(global_=True)
        #     )
        # )

    def process_files(self, files: MarkdownFiles) -> None:
        super().process_files(files)

        for file in files:
            self._replace_backticks(file)

    def _replace_backticks(self, file: MarkdownFile) -> None:
        file.content = re.sub(
            r"\B`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`",
            self._replace_backticks_handler,
            file.content,
        )

    def _replace_backticks_handler(self, match: re.Match) -> str:
        src = match.group(0)
        fqn = match.group(1)

        _LOG.info("processing MD backtick %s", src)
        objects = self._suite.resolve_fqn(fqn)
        if len(objects) > 1:
            _LOG.warning(
                "  found multiple matches for Python FQN <fg=cyan>%s</fg>", fqn
            )
        elif not objects:
            if resolution := resolve_stdlib_module(fqn):
                spec, module_name, attr_name = resolution

                if not is_stdlib_spec(spec):
                    return None

                url = get_stdlib_url(module_name, attr_name)

                _LOG.info("  STDLIB %s", url)

                return "[{}]({})".format(fqn, url)
            else:
                _LOG.info("  No match")
                return src

        link = f'{{@link pydoc:{".".join(x.name for x in objects[0].path)}}}'

        _LOG.info("  LINK %s", link)

        return link

    def _replace_pylink_tag(self, tag: Tag) -> str | None:
        content = tag.args.strip()

        if resolution := resolve_stdlib_module(content):
            spec, module_name, attr_name = resolution

            if is_stdlib_spec(spec):
                return "[{}]({})".format(
                    content, get_stdlib_url(module_name, attr_name)
                )

        return f"{{@link pydoc:{content}}}"
