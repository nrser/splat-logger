"""Functions used only in generating documentation, invoked from
`docs/novella.build`.

To generate docs, from the repo root:

    poetry run novella --directory ./docs

or to serve locally:

    poetry run novella --directory ./docs --serve

"""

from pathlib import Path
import logging
from splatlog._docs.api_page import APIPage
from splatlog._docs.nav import ensure_child_nav, sort_nav

import yaml

REPO_ROOT = Path(__file__).parents[2]
PKG_ROOT = REPO_ROOT / "splatlog"

_LOG = logging.getLogger(__name__)


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
