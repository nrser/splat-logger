import logging
import re
from typing import Optional

from pydoc_markdown.interfaces import Resolver
from pydoc_markdown.util.docspec import ApiSuite
from pydoc_markdown.contrib.processors.crossref import CrossrefProcessor
from docspec import ApiObject

from splatlog._docs.stdlib import get_stdlib_md_link

_LOG = logging.getLogger(__name__)


class DocstringBacktickProcessor(CrossrefProcessor):
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
            src = match.group(0)
            name = match.group(1)

            _LOG.info("processing SRC backtick %s", src)

            if self.resolver_v2:
                target = self.resolver_v2.resolve_reference(suite, node, name)
                if target:
                    link = f'{{@link pydoc:{".".join(x.name for x in target.path)}}}'

                    _LOG.info("  LINK %s", link)

                    return link

            elif resolver:
                href = resolver.resolve_ref(node, name)
                if href:
                    _LOG.info("  HREF %s", href)

                    return "[`{}`]({})".format(name, href)

            if stdlib_link := get_stdlib_md_link(name):
                return stdlib_link

            _LOG.info("  No match")
            return src

        node.docstring.content = re.sub(
            r"\B`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`",
            handler,
            node.docstring.content,
        )
