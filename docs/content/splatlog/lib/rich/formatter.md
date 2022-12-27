splatlog.lib.rich.formatter.RichFormatter
==============================================================================

Examples
------------------------------------------------------------------------------

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

### Prelude ###

Before anything we need to import `splatlog.lib.rich.inline.InlineFormatter`, as
well as the standard library modules that we'll use in the examples.

```python
>>> from typing import *
>>> from dataclasses import dataclass

>>> import rich
>>> from rich.text import Text

>>> from splatlog.lib.rich.formatter import RichFormatter

```

### General Use ###

`RichFormatter` instances combine literal text and interpolated objects into
`rich.text.Text` instances. By default interpolated objects are formatted with
`repr` and highlighted with `rich.highlighter.ReprHighlighter`.

Let's take a look at a _dataclass_, where the `dataclasses.dataclass` decorator
has generated a nice `__repr__` implementation for us.

> You won't be able to see the highlight coloring here because it's
> automatically stripped when writing to `sys.stdout` in the `doctest` (and it
> seems like it would be quite a pain to test for the control codes in the
> test), so you'll have to just trust us it will appear in normal use.

```python
>>> formatter = RichFormatter()

>>> @dataclass
... class Point:
...     x: float
...     y: float

>>> point = Point(x=1.23, y=4.56)
>>> text = formatter.format("The point is: {}, cool huh?", point)
>>> isinstance(text, Text)
True
>>> rich.print(text)
The point is: Point(x=1.23, y=4.56), cool huh?

```

> 📝 NOTE
> 
> Dataclasses are used in many of these examples simply due to their concise
> definitions. Unless otherwise mentioned the same approach applies to "normal"
> classes as well.

### Conversions and Custom Representations ###

As of writing (2022-12-23, Python 3.10), `string.Formatter` defines three
_conversions_, invoked by a formate string suffix of `!` followed by the
conversion character:

1.  `!r` — `repr` conversion.
2.  `!s` — `str` conversion.
3.  `!a` — `ascii` conversion.

All are supported, as well as overriding or providing additional conversions
via the `RichFormatter` constructor.

#### `!r` — `repr` Conversion ####

As mentioned above, `RichFormatter` uses `repr` formatting by default, so the
`!r` conversion has no effect.

```python
>>> rich.print(formatter.format("The point is: {!r}, cool huh?", point))
The point is: Point(x=1.23, y=4.56), cool huh?

```

#### `!s` — `str` Conversion ####

The `!s` conversion calls `str` on the interpolated object and wraps the result
in a `rich.text.Text`, without applying any highlighting.

To demonstrate, we define a class with a custom `__str__` implementation.

```python
>>> class SomeClass:
...     name: str
...     
...     def __init__(self, name: str):
...         self.name = name
...     
...     def __str__(self) -> str:
...         return f"{self.__class__.__name__} named '{self.name}'"

>>> rich.print(
...     formatter.format("We got {!s} over here!", SomeClass(name="Classy Class"))
... )
We got SomeClass named 'Classy Class' over here!

```

#### `!a` — `ascii` Conversion ####

Just like `!r`, but uses `ascii` to generate the highlighted string.

```python
>>> @dataclass
... class UnicodeNamed:
...     name: str
    
>>> rich.print(
...     formatter.format(
...         "Lookin' at {!a} in ascii.", UnicodeNamed(name="λ")
...     )
... )
Lookin' at UnicodeNamed(name='\u03bb') in ascii.

```

#### Custom Conversions ####

For no really good reason, you can add or override conversions in the
`RichFormatter` constructor.

Conversions take the type `splatlog.lib.rich.formatter.RichFormatterConverter`,
which has form

    (typing.Any) -> rich.text.Text
    
and you need to provide a mapping of `str` to converter, which is merged over
the standard conversions, allowing you to override them if you really want.

```python
>>> weird_formatter = RichFormatter(
...     conversions=dict(
...         m=lambda v: Text.from_markup(str(v)),
...     ),
... )

>>> @dataclass
... class Smiles:
...     name: str
...     
...     def __str__(self) -> str:
...         return f":smile: {self.name} :smile:"

>>> rich.print(
...     weird_formatter.format("Hello, my name is {!s}", Smiles(name="nrser"))
... )
Hello, my name is :smile: nrser :smile:

>>> rich.print(
...     weird_formatter.format("Hello, my name is {!m}", Smiles(name="nrser"))
... )
Hello, my name is 😄 nrser 😄

```

### Rich Text Protocol (`__rich_text__` Methods) ###

For full control of formatting classes can implement the
`splatlog.lib.rich.formatter.RichText` protocol, which consists of defining
a single method `__rich_text__` that takes no arguments and returns a
`rich.text.Text` instance.

```python
>>> @dataclass
... class CustomFormatted:
...     name: str
...     
...     def __rich_text__(self) -> Text:
...         return Text.from_markup(f":smile: {self.name} :smile:")

>>> custom_formatted = CustomFormatted(name="Hey yo!")
>>> rich.print(
...     formatter.format(
...         "Rendered with RichText protocol: {}. Pretty neat!",
...         custom_formatted
...     )
... )
Rendered with RichText protocol: 😄 Hey yo! 😄. Pretty neat!

```

`RichText` is a `typing.Protocol` that is `typing.runtime_checkable`, allowing
`isinstance` checks, should you have a use for them.

```python
>>> from splatlog.lib.rich.formatter import RichText
>>> isinstance(custom_formatted, RichText)
True

```

### Rich Repr Protocol (`__rich_repr__` Methods) ###



[Rich Repr Protocol]: https://rich.readthedocs.io/en/latest/pretty.html?highlight=__rich_repr__#rich-repr-protocol

```python
>>> from rich.repr import RichReprResult

>>> class RichRepred:
...     BEST_NAME = "nrser"
...     BEST_QUEST = "get rich"
...     BEST_COLOR = "blue"
...     
...     name: str
...     quest: str
...     fav_color: str
...
...     def __init__(
...         self,
...         name: str,
...         quest: str = BEST_QUEST,
...         fav_color: str = BEST_COLOR,
...     ):
...         self.name = name
...         self.quest = quest
...         self.fav_color = fav_color
...     
...     def __rich_repr__(self) -> RichReprResult:
...         yield "name", self.name
...         yield "quest", self.quest, self.BEST_QUEST
...         yield "fav_color", self.fav_color, self.BEST_COLOR

>>> using_defaults = RichRepred(name="nrser")

>>> rich.print(formatter.format("Got {} here!", using_defaults))
Got RichRepred(name='nrser') here!


```

Reference
------------------------------------------------------------------------------

@pydoc splatlog.lib.rich.formatter
