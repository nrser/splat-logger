from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import logging
import sys
from typing import IO, Optional
from splatlog._docs.nav import dig_nav

import yaml

REPO_ROOT = Path(__file__).parents[2]
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
