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
