Basic Usage
==============================================================================

```python
>>> import sys
>>> import splatlog

>>> log = splatlog.getLogger("splatlog.doc.basic_usage")

>>> splatlog.setup(
...     console=sys.stdout,
...     verbosityLevels={
...         "splatlog": (
...             (0, splatlog.WARNING),
...             (1, splatlog.INFO),
...             (2, splatlog.DEBUG),
...         ),
...     },
...     verbosity=1,
... )

>>> log.info("Hey ya!")
    INFO      splatlog.doc.basic_usage
    msg       Hey ya!

>>> log.debug("Won't show, because verbosity's too low!")

>>> splatlog.setVerbosity(2)
>>> log.debug(
...     "Ok, now we should see it",
...     verbosity=splatlog.getVerbosity(),
...     effectiveLevel=log.getEffectiveLevel(),
... )
    DEBUG     splatlog.doc.basic_usage
    msg       Ok, now we should see it
    data      effectiveLevel    int     10
              verbosity         int     2

```
