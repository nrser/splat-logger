"""Functions used only in generating documentation, invoked from
`docs/novella.build`.

To generate docs, from the repo root:

    poetry run novella --directory ./docs

or to serve locally:

    poetry run novella --directory ./docs --serve

"""

from pathlib import Path
import logging

import yaml

REPO_ROOT = Path(__file__).parents[1]
PKG_ROOT = REPO_ROOT / "splatlog"
DOCS_DIR = REPO_ROOT / "docs"
CONTENT_DIR = DOCS_DIR / "content"
MKDOCS_YML = DOCS_DIR / "mkdocs.yml"

_LOG = logging.getLogger(__name__)


def generate_api_pages(build_dir: Path) -> None:
    mkdocs_yml_path = build_dir / "mkdocs.yml"
    mkdocs_config = yaml.safe_load(mkdocs_yml_path.open("r", encoding="utf-8"))

    _LOG.info("Loaded mkdocs config\n\n%s", yaml.safe_dump(mkdocs_config))

    md_paths = add_api_nav(mkdocs_config)

    yaml.safe_dump(mkdocs_config, mkdocs_yml_path.open("w", encoding="utf-8"))

    for py_rel_path, md_rel_path in md_paths:
        md_path = build_dir / "content" / md_rel_path

        if not md_path.exists():
            if py_rel_path.name == "__init__.py":
                module_name = str(py_rel_path.parent).replace("/", ".")
            else:
                module_name = str(py_rel_path.with_suffix("")).replace("/", ".")

            md_path.parent.mkdir(parents=True, exist_ok=True)

            with md_path.open("w", encoding="utf-8") as file:
                print(f"`{module_name}` Module", file=file)
                print("=" * 78, file=file)
                print("", file=file)
                print(f"@pydoc {module_name}", file=file)


def iter_py_files():
    for path in PKG_ROOT.glob("**/*.py"):
        yield path.relative_to(REPO_ROOT)


def list_py_files():
    return list(iter_py_files())


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


def load_mkdocs_config():
    return yaml.safe_load(MKDOCS_YML.open("r", encoding="utf-8"))


def get_name(py_path):
    if py_path.name == "__init__.py":
        return "index"
    return py_path.stem


def add_api_nav(mkdocs_config):
    api_nav_root = ensure_child_nav(mkdocs_config["nav"], "API Documentation")
    md_paths = []

    for rel_path in iter_py_files():
        parent_nav = dig_nav(api_nav_root, rel_path.parent.parts)
        name = get_name(rel_path)

        if name_nav := get_child_nav(parent_nav, name):
            md_path = rel_path.parent / name / "index.md"
            name_nav.append(str(md_path))
            md_paths.append((rel_path, md_path))

        else:
            md_path = rel_path.parent / f"{name}.md"
            if name == "index":
                parent_nav.append(str(md_path))
            else:
                parent_nav.append({name: str(md_path)})
            md_paths.append((rel_path, md_path))

    sort_nav(api_nav_root)
    return md_paths


def nav_sort_key(entry):
    if isinstance(entry, dict):
        name, contents = list(entry.items())[0]
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
            for name, sub_nav in entry.items():
                if isinstance(sub_nav, list):
                    sort_nav(sub_nav)
    nav.sort(key=nav_sort_key)
