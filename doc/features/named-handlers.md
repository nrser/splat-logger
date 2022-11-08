Named Handlers Feature
==============================================================================

Overview
------------------------------------------------------------------------------

Splatlog has an idea of _named handlers_ which:

1.  Have a unique, non-empty `name` (type `str`).
    
2.  Allow get, set and delete by `name`, like a global version of a `property`.
    
3.  Have an associated `cast` function that creates instances from simple and
    convenient values (type `(object) -> None | logging.Handler`).
    
    For instance, a `cast` function might accept a `typing.IO` and return a
    handler that writes to that I/O stream.

There are two built-in _named handlers_:

1.  _console_ — For logging to STDIO. Defaults to using
    `splatlog.rich_handler.RichHandler` to produce nice, tabular output.
    Intended for people to read.
    
2.  _export_ — For exporting logs in machine readable format for another system
    to consume. The `cast` function helps writing JSON to files and streams
    using the `splatlog.json` functionality.

You can easily add your own _named handlers_ as well.

The motivation is:

1.  Encode best practices for configuring handlers for common purposes (I want
    to log to the console, I want to log to a file, etc.).
    
2.  Make handlers easy to access, inspect and replace. 


Usage
------------------------------------------------------------------------------

### Console Handler ###

Say you simply want to log to the console. You can do this:

```python
>>> import splatlog

>>> splatlog.setup(console=True)

```

That creates a `splatlog.rich_handler.RichHandler` logging to `sys.stderr` and
adds it to the root logger. Check it out:

```python
>>> import logging
>>> import sys

>>> console_handler = splatlog.get_named_handler("console")

>>> console_handler in logging.getLogger().handlers
True

>>> console_handler.console.file is sys.stderr
True

```

Since `doctest` doesn't capture STDERR, let's log to STDOUT instead.

```python
>>> splatlog.set_named_handler("console", sys.stdout)

>>> log = splatlog.getLogger(__name__)
>>> log.warning("Now we're talking!")
WARNING   __main__
msg       Now we're talking!

```

Notice that the first handler we created is no logger attached, but our new
STDOUT one is. _Named handlers_ takes care of all this for ya.

```python
>>> console_handler in logging.getLogger().handlers
False

>>> new_console_handler = splatlog.get_named_handler("console")

>>> new_console_handler in logging.getLogger().handlers
True

>>> new_console_handler.console.file is sys.stdout
True

```

You can remove the handler, setting it back to `None` like:

```python
>>> splatlog.set_named_handler("console", None)

```

### Export Handler ###

Suppose you'd like to dump all your logs to a file or stream for processing by
an external system. In this example we use a temporary directory for testing
purposes, and a "pretty" JSON formatting to make the output easier for us humans
to read, but the approach is applicable in general.

First, just some imports and file preperation.

```python
>>> from tempfile import TemporaryDirectory

>>> tmp = TemporaryDirectory()
>>> filename = f"{tmp.name}/log.json"

```

Now we setup Splatlog, setting the level to _DEBUG_ so we get all the logs, and
configuring an _export_ handler to write to our temporary file using the
"pretty" formatting.

```python
>>> splatlog.setup(
...     level=splatlog.DEBUG,
...     export=dict(filename=filename, formatter="pretty")
... )

```

Now let's emit some logs and check out the file contents!

```python
>>> log = splatlog.getLogger(__name__)
>>> log.info("File style!")
>>> log.debug("Some values", x=1, y=22)

>>> with open(filename, "r") as file:
...     print(file.read())
{
    "t": ...,
    "level": "INFO",
    "name": "__main__",
    "file": "<doctest named-handlers.md[...]>",
    "line": 1,
    "msg": "File style!"
}
{
    "t": ...,
    "level": "DEBUG",
    "name": "__main__",
    "file": "<doctest named-handlers.md[...]>",
    "line": 1,
    "msg": "Some values",
    "data": {
        "x": 1,
        "y": 22
    }
}

```

Seems to work pretty well. You can of course setup both _console_ and _export_
handlers; the [verbosity feature](features/verbsoity.md) page has a nice example
using the _verbosity_ system to control log levels in a useful way.

### Custom Handlers ###


