"""Shit just used in generating docs, excluded from the distributed package
(because it depends on dev dependencies).
"""

from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import PackagePath, files

from doctor_genova.external_resolver import ExternalResolution


@dataclass(frozen=True)
class RichResolution:
    BASE_URL = "https://rich.readthedocs.io/en/latest/reference/"

    name: str
    page_module_name: str

    @cached_property
    def page_url(self) -> str:
        if self.page_module_name == "rich":
            return self.BASE_URL + "init.html"
        else:
            return (
                self.BASE_URL + self.page_module_name.split(".")[-1] + ".html"
            )

    def get_name(self) -> str:
        return self.name

    def get_url(self) -> str:
        if self.page_module_name == self.name:
            return self.page_url
        return self.page_url + "#" + self.name

    def get_md_link(self) -> str:
        return "[{}]({})".format(self.name, self.get_url())


class RichResolver:
    @staticmethod
    def as_module_name(file: PackagePath) -> None | str:
        if file.suffix != ".py":
            return None

        if file.parts[0] != "rich":
            return None

        if file.stem == "__init__":
            return ".".join(file.parts[:-1])

        return ".".join(file.with_suffix("").parts)

    def __init__(self):
        metadata_files = files("rich")

        if metadata_files is None:
            raise Exception("rich not found")

        self._module_names = set()

        for file in metadata_files:
            if module_name := self.as_module_name(file):
                self._module_names.add(module_name)

    def resolve_name(self, name: str) -> None | ExternalResolution:
        parts = name.split(".")

        if any(part.startswith("_") for part in parts):
            return None

        length = len(parts)

        if length == 1:
            page_module_name = parts[0]
        else:
            page_module_name = ".".join(parts[:2])

        if page_module_name in self._module_names:
            return RichResolution(
                name=name,
                page_module_name=page_module_name,
            )
