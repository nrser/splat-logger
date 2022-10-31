Basic Usage
==============================================================================

Creating Loggers
------------------------------------------------------------------------------

Use `splatlog` to get loggers the same way you would `logging`.

```python
>>> import splatlog
>>> log = splatlog.getLogger(__name__)

```

Note that loggers returned from `splatlog.getLogger` are
`splatlog.SplatLogger` instances, which are logger _adapters_ rather than being
loggers themselves.

This means that they extend `logging.LoggerAdapter` rather than
`logging.Logger`.

```python
>>> isinstance(log, splatlog.SplatLogger)
True

>>> import logging

>>> isinstance(log, logging.Logger)
False

>>> isinstance(log, logging.LoggerAdapter)
True

>>> isinstance(log.logger, logging.Logger)
True

```

Configuring Output
------------------------------------------------------------------------------

As splatlog sits "on top" of `logging`, you'll need to do some one-time
configuration to add handlers in order to actually see any log output.

In splatlog this function is called `splatlog.setup`, and it serves much the
same purpose as `logging.basicConfig`.

In the following example, we

1.  Set the root logger level to `logging.info`.
    
2.  Tell splatlog to write console output to `sys.stderr`
    
    > Normally we wouldn't need this, but splatlog writes console output to
    > `sys.stderr` by default, and this file is execute via `doctest`, which
    > [does not capture STDERR][1]
    > 
    > [1]: https://docs.python.org/3.10/library/doctest.html#how-are-docstring-examples-recognized
    
3.  Log an _info_ message, along with some data "splatted" in.

```python
>>> import sys
>>> splatlog.setup(level="info", console=sys.stdout)

>>> log.info("Hello world!", x=1, y=2)
INFO        __main__
msg         Hello world!
data        x     int     1
            y     int     2

```

Notice that the log record is rendered in a decently readable tabular format.
We use [rich][] for that. When it's actually in your console it will also have
pretty colors.

[rich]: https://pypi.org/project/rich/

Using Verbosity
------------------------------------------------------------------------------

Besides splatting data into log calls and stylish rendering to consoles,
splatlog has a _verbosity_ system that allows you to configure which loggers
are set to which level as you twist the knob on a single `verbosity` parameter.

Verbosity is an `int` value. It can't be negative, and it must be less than
`sys.maxint`. In practice it usually ranges from `0` to `4`-or-so. The higher
the verbosity, the more logging you see.

Verbosity is directly inspired by the `-v`, `-vv`, `-vvv`, ... pattern of option
flags common in *nix command line interfaces.

To use verbosity, you pass a `verbosityLevels` mapping to `splatlog.setup`.

Each key is the `logging.Logger.name` of the logger it applies to. The
coresponding value is a sequence of `tuple` pairs. The first entry in the pair
is a verbosity integer, and the second entry is the log level to take effect at
that verbosity.

```python
>>> log = splatlog.getLogger(name="splatlog.doc.basic_usage")

>>> import sys

>>> splatlog.setup(
...     console=sys.stdout,
...     verbosityLevels={
...         "splatlog": (
...             (0, splatlog.WARNING),
...             (1, splatlog.INFO),
...             (2, splatlog.DEBUG),
...         ),
...     },
... )

>>> log.info("Hey ya!")
INFO        splatlog.doc.basic_usage
msg         Hey ya!

>>> log.debug("Won't show, because verbosity's too low!")

>>> splatlog.setVerbosity(2)
>>> log.debug(
...     "Ok, now we should see it",
...     verbosity=splatlog.getVerbosity(),
...     effectiveLevel=log.getEffectiveLevel(),
... )
DEBUG       splatlog.doc.basic_usage
msg         Ok, now we should see it
data        effectiveLevel    int     10
            verbosity         int     2

```

```python
>>> splatlog.delVerbosityLevels(unsetLoggerLevels=True)
>>> splatlog.delVerbosity()

>>> splatlog.setup(
...     level=splatlog.DEBUG,
...     console=dict(
...         console="stdout",
...         verbosityLevels={
...             "splatlog": (
...                 (0, splatlog.WARNING),
...                 (1, splatlog.INFO),
...                 (2, splatlog.DEBUG),
...             ),
...         },
...     ),
...     verbosity=0,
... )

>>> log.warning("Watch out now!")
    WARNING     splatlog.doc.basic_usage
    msg         Watch out now!

>>> log.debug("Won't show, because verbosity's too low!")

>>> splatlog.setVerbosity(2)

>>> log.debug(
...     "Ok, now we should see it",
...     verbosity=splatlog.getVerbosity(),
... )
DEBUG       splatlog.doc.basic_usage
msg         Ok, now we should see it
data        verbosity         int     2

```
