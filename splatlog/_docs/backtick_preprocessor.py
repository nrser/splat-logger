import logging
import re
from typing import Callable, Iterable, TypeVar

from novella.markdown.preprocessor import MarkdownFile, MarkdownFiles
from novella.markdown.tagparser import Tag
from pydoc_markdown.contrib.renderers.markdown import MarkdownReferenceResolver
from pydoc_markdown.novella.preprocessor import PydocTagPreprocessor

from splatlog._docs.docstring_backtick_processor import (
    DocstringBacktickProcessor,
)
from splatlog._docs.stdlib import (
    get_stdlib_url,
    is_stdlib_spec,
    resolve_stdlib_module,
)

_LOG = logging.getLogger(__name__)

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
    """TODO Need something here for linking tests"""

    def __post_init__(self) -> None:
        super().__post_init__()

        # Add a processor to be run on source file docstrings; it looks for
        # `...` in the strings and attempts to resolve them against both the
        # package 'suite' and the Python stdlib
        self._processors.append(
            DocstringBacktickProcessor(
                resolver_v2=MarkdownReferenceResolver(global_=True)
            )
        )

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
