from dataclasses import dataclass
import logging
import re
from typing import Optional

from pydoc_markdown.util.docspec import ApiSuite
from pydoc_markdown.interfaces import Processor, Resolver, ResolverV2
import docspec

from splatlog._docs.stdlib_resolver import StdlibResolver

_LOG = logging.getLogger(__name__)


@dataclass
class DocstringBacktickProcessor(Processor):
    BACKTICK_RE = re.compile(
        r"\B`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`"
    )

    resolver_v2: ResolverV2
    stdlib_resolver: StdlibResolver

    def process(
        self, modules: list[docspec.Module], resolver: Optional[Resolver]
    ) -> None:
        docspec.visit(
            modules,
            lambda x: self._preprocess_refs(x, ApiSuite(modules)),
        )

    def _preprocess_refs(
        self,
        node: docspec.ApiObject,
        suite: ApiSuite,
    ) -> None:
        if not node.docstring:
            return

        def handler(match: re.Match) -> str:
            src = match.group(0)
            name = match.group(1)

            _LOG.info("processing SRC backtick %s", src)

            if self.resolver_v2:
                api_object = self.resolver_v2.resolve_reference(
                    suite, node, name
                )

                if api_object:
                    link = "{{@link pydoc:{}}}".format(
                        ".".join(x.name for x in api_object.path)
                    )

                    _LOG.info(
                        "  <fg=green>TAG</fg> <fg=cyan>%s</fg> -> <fg=green>%s</fg>",
                        name,
                        link,
                    )

                    return link

            if resolution := self.stdlib_resolver.resolve_name(name):
                _LOG.info(
                    "  <fg=magenta>STDLIB</fg> <fg=cyan>%s</fg> -> <fg=magenta>%s</fg>",
                    name,
                    resolution.md_link,
                )

                return resolution.md_link

            _LOG.info("  <fg=red>NO MATCH</fg>")
            return src

        node.docstring.content = self.BACKTICK_RE.sub(
            handler,
            node.docstring.content,
        )
