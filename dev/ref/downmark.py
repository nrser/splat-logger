from collections.abc import Iterable

INDENT_SIZE = 4
INDENT = " " * INDENT_SIZE


def render_list_line(content, depth) -> str:
    return f"{INDENT * depth}-   {content}"


def render_list_lines(iterable: Iterable, *, _depth: int = 0):
    for entry in iterable:
        if isinstance(entry, Iterable) and not isinstance(entry, (str, bytes)):
            yield from render_list_lines(entry, _depth=_depth + 1)
        else:
            yield render_list_line(entry, _depth)


def render_list(*entries) -> str:
    """
    ```python
    >>> print(
    ...     render_list(
    ...         "Item 1",
    ...         "Item 2",
    ...         ("Item 2.1", "Item 2.2", ("Item 2.2.1",)),
    ...         "Item 3",
    ...         ("Item 3.1",),
    ...         "Item 4",
    ...     )
    ... )
    -   Item 1
    -   Item 2
        -   Item 2.1
        -   Item 2.2
            -   Item 2.2.1
    -   Item 3
        -   Item 3.1
    -   Item 4

    >>> print(
    ...     render_list(
    ...         "Must be negative",
    ...         ("`name` Attribute", ("Must be 'not_gonna_happen'",)),
    ...         ("`suffix` Attribute", ("Must be 'not_gonna_happen'",)),
    ...         ("Any of:",  ("Must be in range(0, 10)", "Must be even")),
    ...     )
    ... )
    -   Must be negative
    -   `name` Attribute
        -   Must be 'not_gonna_happen'
    -   `suffix` Attribute
        -   Must be 'not_gonna_happen'
    -   Any of:
        -   Must be in range(0, 10)
        -   Must be even

    # >>> print(
    # ...     render_list(
    # ...         (None, "Must be negative"),
    # ...         ("`name` Attribute", "Must be 'not_gonna_happen'"),
    # ...         ("`suffix` Attribute", "Must be 'not_gonna_happen'"),
    # ...         ("Any of:",  "Must be in range(0, 10)"),
    # ...         ("Any of:",  "Must be even"),
    # ...         (("`blah` Attribute", "Any of:"), "Some problem"),
    # ...         (("`blah` Attribute", "Any of:"), "Some other problem"),
    # ...     )
    # ... )
    # -   Must be negative
    # -   `name` Attribute
    #     -   Must be 'not_gonna_happen
    # -   `suffix` Attribute
    #     -   Must be 'not_gonna_happen'
    # -   Any of:
    #     -   Must be in range(0, 10)
    #     -   Must be even
    # -   `blah` Attribute
    #     - Any of:
    #         - Some problem
    #         - Some other problem

    ```
    """
    return "\n".join(render_list_lines(entries))
