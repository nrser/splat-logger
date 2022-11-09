"""Functions used only in generating documentation, invoked from
`docs/novella.build`.

To generate docs, from the repo root:

    poetry run novella --directory ./docs

or to serve locally:

    poetry run novella --directory ./docs --serve

"""

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import logging
import sys
from typing import IO, Optional

import yaml

REPO_ROOT = Path(__file__).parents[1]
PKG_ROOT = REPO_ROOT / "splatlog"

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class APIPage:
    @classmethod
    def logger(cls) -> logging.Logger:
        return _LOG.getChild(cls.__qualname__)

    module_rel_path: Path
    build_dir: Path

    @cached_property
    def is_init(self) -> bool:
        return self.module_rel_path.name == "__init__.py"

    @cached_property
    def module_name(self) -> str:
        if self.is_init:
            path = self.module_rel_path.parent
        else:
            path = self.module_rel_path.with_suffix("")
        return str(path).replace("/", ".")

    @cached_property
    def name(self) -> str:
        if self.is_init:
            return "index"
        return self.module_rel_path.stem

    @cached_property
    def title(self) -> str:
        return self.module_name

    @cached_property
    def metadata(self) -> dict[str, str]:
        return {"title": self.title}

    @cached_property
    def nav_title(self) -> Optional[str]:
        if self.is_init:
            return None
        return self.name

    @cached_property
    def content_dir(self) -> Path:
        return self.build_dir / "content"

    @cached_property
    def path(self) -> Path:
        as_dir = self.content_dir / self.module_rel_path.parent / self.name

        if as_dir.exists():
            return as_dir / "index.md"

        return (
            self.content_dir / self.module_rel_path.parent / (self.name + ".md")
        )

    @cached_property
    def rel_path(self) -> Path:
        return self.path.relative_to(self.content_dir)

    def print_stub(self, file: IO[str] = sys.stdout) -> None:
        print("---", file=file)
        yaml.safe_dump(self.metadata, file)
        print("---", file=file)
        print("", file=file)

        print(self.title, file=file)
        print("=" * 78, file=file)
        print("", file=file)

        print(f"@pydoc {self.module_name}", file=file)
        print("", file=file)

    def generate(self) -> bool:
        log = self.logger().getChild("generate")

        if self.path.exists():
            log.info("Page %s exists at %s", self.module_name, self.rel_path)
            return False

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as file:
            self.print_stub(file)

        log.info("Generated %s page at %s", self.module_name, self.rel_path)

        return True

    def add_to_api_nav(self, api_nav: list) -> None:
        parent_nav = dig_nav(api_nav, self.rel_path.parent.parts)

        if self.nav_title:
            parent_nav.append({self.nav_title: str(self.rel_path)})
        else:
            parent_nav.append(str(self.rel_path))


def generate_api_pages(build_dir: Path) -> None:
    mkdocs_yml_path = build_dir / "mkdocs.yml"
    mkdocs_config = yaml.safe_load(mkdocs_yml_path.open("r", encoding="utf-8"))
    api_nav = ensure_child_nav(mkdocs_config["nav"], "API Documentation")

    _LOG.info("Loaded mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))

    pages = [APIPage(p, build_dir) for p in iter_py_files()]

    for page in pages:
        page.generate()
        page.add_to_api_nav(api_nav)

    sort_nav(api_nav)
    yaml.safe_dump(mkdocs_config, mkdocs_yml_path.open("w", encoding="utf-8"))

    _LOG.info("Updated mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))


def iter_py_files():
    for path in PKG_ROOT.glob("**/*.py"):
        yield path.relative_to(REPO_ROOT)


def get_child_nav(nav, name):
    for entry in nav:
        if isinstance(entry, dict) and name in entry:
            return entry[name]
    return None


def ensure_child_nav(nav, name):
    if child_nav := get_child_nav(nav, name):
        return child_nav
    child_nav = []
    nav.append({name: child_nav})
    return child_nav


def dig_nav(nav, key_path):
    target = nav
    for key in key_path:
        target = ensure_child_nav(target, key)
    return target


def nav_sort_key(entry):
    if isinstance(entry, dict):
        name = next(iter(entry.keys()))
        if name.startswith("_"):
            return (3, name)
        return (2, name)
    else:
        path = Path(entry)
        if path.stem == "index":
            return (1, "index")
        if path.stem.startswith("_"):
            return (3, path.stem)
        return (2, path.stem)


def sort_nav(nav):
    for entry in nav:
        if isinstance(entry, dict):
            for _name, sub_nav in entry.items():
                if isinstance(sub_nav, list):
                    sort_nav(sub_nav)
    nav.sort(key=nav_sort_key)
