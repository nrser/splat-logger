"""Functions used only in generating documentation, invoked from
`docs/novella.build`.

To generate docs, from the repo root:

    poetry run novella --directory ./docs

or to serve locally:

    poetry run novella --directory ./docs --serve

### Python File Linking Tests ###

We are in a **_source file_** (`splatlog/**/*.py`) docstring here.

1.  Hash Linking

    1.  Local hash-linking (resolved by scope) ✅

        #BacktickPreprocessor

    2.  Fully-qualified hash-linking ✅

        #splatlog.rich_handler.RichHandler

    3.  Stdlib hash-linking ✅

        #typing.IO

2.  `@pylink` Tag Linking

    > The fact these work at all seem incidental... they happen to be scanned
    > later as part of the general markdown pre-processing, which successfully
    > replaces the fully-qualified ones.

    1.  Local `@pylink` tag (resolved by scope) ❌

        {@pylink BacktickPreprocessor}

        > This does not work because tags are not picked up at all in source
        > pre-processing, so the local resolution can't happen.

    2.  Fully-qualified `@pylink` tag ✅

        {@pylink splatlog.rich_handler.RichHandler}

    3.  Stdlib `@pylink` tag ✅

        {@pylink typing.IO}

3.  Backtick Linking

    1.  Local backtick ✅

        `BacktickPreprocessor`

    2.  Fully-qualified backtick ✅

        `splatlog.rich_handler.RichHandler`

    3.  Stdlib backtick ✅

        `typing.IO`

"""

from pathlib import Path
import logging

from pydoc_markdown.novella.preprocessor import PydocTagPreprocessor
from pydoc_markdown.contrib.renderers.markdown import MarkdownReferenceResolver

from splatlog._docs.api_page import APIPage
from splatlog._docs.nav import ensure_child_nav, sort_nav
from splatlog._docs.stdlib_processor import MyProcessor
from splatlog._docs.backtick_preprocessor import BacktickPreprocessor

import yaml

REPO_ROOT = Path(__file__).parents[2]
PKG_ROOT = REPO_ROOT / "splatlog"

_LOG = logging.getLogger(__name__)


def add_processor(preprocessor: PydocTagPreprocessor):
    preprocessor._processors.append(
        MyProcessor(resolver_v2=MarkdownReferenceResolver(global_=True))
    )


def generate_api_pages(build_dir: Path) -> None:
    mkdocs_yml_path = build_dir / "mkdocs.yml"
    mkdocs_config = yaml.safe_load(mkdocs_yml_path.open("r", encoding="utf-8"))
    api_nav = ensure_child_nav(mkdocs_config["nav"], "API Documentation")

    _LOG.debug("Loaded mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))

    pages = [APIPage(p, build_dir) for p in iter_py_files()]

    for page in pages:
        page.generate()
        page.add_to_api_nav(api_nav)

    sort_nav(api_nav)

    # Doesn't work...
    # mkdocs_config["watch"] = [str(PKG_ROOT)]

    yaml.safe_dump(mkdocs_config, mkdocs_yml_path.open("w", encoding="utf-8"))

    _LOG.debug("Updated mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))


def iter_py_files():
    for path in PKG_ROOT.glob("**/*.py"):
        yield path.relative_to(REPO_ROOT)
