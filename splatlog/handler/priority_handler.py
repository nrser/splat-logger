from logging import NOTSET, FileHandler, Handler, Manager, StreamHandler
from typing import Optional


class PriorityHandler(Handler):
    """
    A handler with a log level that is _independent_ of the logger(s) it is
    attached to. As the name suggests, this was created for connecting to a
    monitoring system, where we may want that system to receive _more_ levels
    than the main logs.

    The simplest use case being "always send everything" to the monitoring
    system.

    This requires integration with logger instances that the monitoring handler
    belongs to, hence this class will only operate as specified when it belongs
    to a `SplatLogger` or logger class with similar support.
    """

    manager: Optional[Manager] = None

    def setLevel(self, level):
        """
        Set the logging level of this handler.  level must be an int or a str.
        """
        super().setLevel(level)
        if self.manager is not None:
            self.manager._clear_cache()


class PriorityStreamHandler(PriorityHandler, StreamHandler):
    pass


class PriorityFileHandler(PriorityHandler, FileHandler):
    pass
