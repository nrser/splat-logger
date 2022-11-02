"""Helpers for working with logger / module names.

Convention is to use module names as logger names, so they're kinda the same
thing in practice.
"""


def root_name(module_name: str) -> str:
    """Get the first element of a module name.

    ##### Examples #####

    ```python
    >>> root_name("splatlog.names")
    'splatlog'

    ```
    """
    return module_name.split(".")[0]


def is_in_hierarchy(hierarchy_name: str, logger_name: str):
    """
    ##### Examples #####

    ```python
    >>> is_in_hierarchy("splatlog", "splatlog")
    True

    >>> is_in_hierarchy("splatlog", "splatlog.names")
    True

    >>> is_in_hierarchy("blah", "splatlog")
    False

    >>> is_in_hierarchy("splat", "splatlog")
    False

    ```
    """
    if not logger_name.startswith(hierarchy_name):
        return False
    hierarchy_name_length = len(hierarchy_name)
    return (
        hierarchy_name_length == len(logger_name)  # same as == at this point
        or logger_name[hierarchy_name_length] == "."
    )
