`splatlog.lib.text.fmt_type_hint` Examples
==============================================================================

> 📝 NOTE
> 
> You can verify these example using [doctest][] with a command similar to
> 
>       python -m doctest -v -o NORMALIZE_WHITESPACE -o ELLIPSIS <file>
> 
> [doctest]: https://docs.python.org/3.10/library/doctest.html
> 
> Note that `splatlog` and it's dependencies must be available to Python. If 
> you've checked out the repository just stick `poetry run` in front of the
> command and it should work.
> 

Prelude
------------------------------------------------------------------------------

Before anything we need to import `splatlog.lib.validate`, as well as the
standard library modules that we'll use in the examples.

```python
>>> from pathlib import Path
>>> from splatlog.lib.validate import *

```

`splatlog.lib.validate.validate`
------------------------------------------------------------------------------

The basic `splatlog.lib.validate.validate` function takes a predicate and a
failure message to emit if the predicate returns a false-like value.

```python
>>> validate_even = validate(lambda x: x % 2 == 0, "must be even")

>>> failures = validate_even(0)
>>> failures.is_empty()
True

>>> failures = validate_even(1)
>>> failures.is_empty()
False
>>> list(failures)
['must be even']

>>> failures = validate_even(None)
>>> failures.is_empty()
Traceback (most recent call last):
    ...
TypeError: unsupported operand type(s) for %: 'NoneType' and 'int'

```

Validators are made to be composed. `validate_optional` wraps around another
validator and accepts `None` in addition to whataver the provided validator
accepts.

```python
>>> validate_optional_even = validate_optional(validate_even)
>>> failures = validate_optional_even(None)
>>> failures.is_empty()
True

```

```python
>>> v = validate_any_of(
...     validate_in(range(10)),
...     validate(lambda x: x % 2 == 0, "Must be even"),
... )

>>> failures = v(1)
>>> failures.is_empty()
True

>>> failures = v(11)
>>> failures.is_empty()
False
>>> print_failures(failures)
-   any of
    -   Must be in range(0, 10)
    -   Must be even

```

```python
>>> validate(lambda v: v > 0, "Is positive")(123).is_empty()
True

```

```python

>>> failures = validate(lambda v: v < 0, "Must be negative")(123)
>>> list(failures)
['Must be negative']

```

```python

>>> from pathlib import Path
>>> v = validate_attr(
...     ("name", "suffix"),
...     validate(
...         lambda v: v == "not_gonna_happen",
...         "must be 'not_gonna_happen'"
...     )
... )
>>> f = v(Path("/a/b/c"))
>>> list(f.items())
[((<Failures name='`.name`'>,), "must be 'not_gonna_happen'"),
    ((<Failures name='`.suffix`'>,), "must be 'not_gonna_happen'")]

```

```python

>>> v = validate_any_of(
...     validate_in(range(10)),
...     validate(lambda x: x % 2 == 0, "Must be even"),
... )
>>> f = v(11)
>>> list(f.items())
[((<Failures name='any of'>,), 'Must be in range(0, 10)'),
    ((<Failures name='any of'>,), 'Must be even')]

```

```python
>>> v = validate_attr(
...     "name",
...     validate_any_of(
...         validate_length(max=0),
...         validate(
...             lambda v: v == "not_gonna_happen",
...             "must be 'not_gonna_happen'"
...         ),
...     )
... )
>>> f = v(Path("/a/b/c"))
>>> list(f.items())
[((<Failures name='`.name`'>,), 'Length must be at most 0'),
    ((<Failures name='`.name`'>,), "must be 'not_gonna_happen'")]

```

```python
>>> v = validate_any_of(
...     validate_attr(
...         "name",
...         validate_length(max=0),
...     ),
...     validate_attr(
...         "suffix",
...         validate(
...             lambda v: v == "not_gonna_happen",
...             "must be 'not_gonna_happen'"
...         ),
...     ),
... )
>>> f = v(Path("/a/b/c"))
>>> list(f.items())
[((<Failures name='any of'>, <Failures name='`.name`'>),
        'Length must be at most 0'),
    ((<Failures name='any of'>, <Failures name='`.suffix`'>),
        "must be 'not_gonna_happen'")]

```

