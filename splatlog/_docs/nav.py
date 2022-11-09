from pathlib import Path


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
