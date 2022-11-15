import logging
import re
from typing import Callable, Iterable, Optional, TypeVar

from novella.markdown.preprocessor import MarkdownFile, MarkdownFiles
from novella.markdown.tagparser import Tag
from pydoc_markdown.contrib.renderers.markdown import MarkdownReferenceResolver
from pydoc_markdown.novella.preprocessor import PydocTagPreprocessor
from docspec import Indirection, ApiObject
from pydoc_markdown.util.docspec import ApiSuite

from splatlog._docs.docstring_backtick_processor import (
    DocstringBacktickProcessor,
)
from splatlog._docs.stdlib_resolver import StdlibResolver

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
    """Replaces simple backtick spans with links when they seem to point to:

    1.  Another object in the documented package.
    2.  An object in the Python standard library.

    """

    _stdlib_resolver: StdlibResolver

    def __post_init__(self) -> None:
        super().__post_init__()

        self._stdlib_resolver = StdlibResolver()

        # Add a processor to be run on source file docstrings; it looks for
        # `...` in the strings and attempts to resolve them against both the
        # package 'suite' and the Python stdlib
        self._processors.append(
            DocstringBacktickProcessor(
                resolver_v2=MarkdownReferenceResolver(global_=True),
                stdlib_resolver=self._stdlib_resolver,
            )
        )

    def process_files(self, files: MarkdownFiles) -> None:
        super().process_files(files)

        # NOTE  `PydocTagProcessor.process_files` filters the modules list,
        #       removing anything that doesn't have a docstring... which is
        #       generally nice — lots of junk pops up if you don't — but it
        #       removed indirections as well, which we need to resolve indirect
        #       links.
        #
        #       There is a better way to do this for sure, but for now we simply
        #       overwrite the suite with a new, complete one.
        #
        self._suite = ApiSuite(list(self._loader.load()))

        for file in files:
            self._replace_backticks(file)

    def _replace_backticks(self, file: MarkdownFile) -> None:
        file.content = DocstringBacktickProcessor.BACKTICK_RE.sub(
            self._replace_backticks_handler,
            file.content,
        )

    def _resolve_fqn(self, fqn: str) -> Optional[ApiObject]:
        objects = self._suite.resolve_fqn(fqn)

        count = len(objects)

        if count == 0:
            return None

        if count > 1:
            _LOG.warning(
                "  found multiple matches for Python FQN <fg=cyan>%s</fg>", fqn
            )

        return objects[0]

    def _resolve_link(self, fqn: str) -> Optional[str]:
        if api_object := self._resolve_fqn(fqn):
            if isinstance(api_object, Indirection):
                _LOG.info(
                    "  <fg=yellow>INDIRECTION</fg> <fg=cyan>%s</fg> -> <fg=yellow>%s</fg>",
                    fqn,
                    api_object.target,
                )
                return self._resolve_link(api_object.target)

            else:
                link = "{{@link pydoc:{}}}".format(
                    ".".join(x.name for x in api_object.path)
                )

                _LOG.info(
                    "  <fg=green>TAG</fg> <fg=cyan>%s</fg> -> <fg=green>%s</fg>",
                    fqn,
                    link,
                )

                return link

        else:
            if resolution := self._stdlib_resolver.resolve_name(fqn):
                _LOG.info(
                    "  <fg=magenta>STDLIB</fg> <fg=cyan>%s</fg> -> <fg=magenta>%s</fg>",
                    fqn,
                    resolution.md_link,
                )
                return resolution.md_link

            else:
                _LOG.info("  <fg=red>NO MATCH</fg>")
                return None

    def _replace_backticks_handler(self, match: re.Match) -> str:
        src = match.group(0)
        fqn = match.group(1)

        _LOG.info("processing MD backtick <fg=cyan>%s</fg>", src)

        if link := self._resolve_link(fqn):
            return link
        else:
            return src

    def _replace_pylink_tag(self, tag: Tag) -> str | None:
        """
        Override `PydocTagPreprocessor._replace_pylink_tag` to check if the
        link content is a Python stdlib path, and use that if so.

        This is not ideal, because it actually allows stdlib to shaddow the
        package in case of conflict, which is probably backwards of what you
        would expect, but it's simple as an initial version.
        """
        content = tag.args.strip()

        if resolution := self._stdlib_resolver.resolve_name(content):
            return resolution.md_link

        return f"{{@link pydoc:{content}}}"
