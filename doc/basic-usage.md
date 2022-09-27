Basic Usage
==============================================================================

```python
>>> import sys
>>> import splatlog

>>> log = splatlog.setup(
...     loggerName="splatlog.doc.basic_usage",
...     roleName="app",
...     console=sys.stdout,
... )

>>> log.info("Hey ya!")
    INFO      splatlog.doc.basic_usage
    msg       Hey ya!

```
