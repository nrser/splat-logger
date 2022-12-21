"""Root of the `splatlog` package.

Imports pretty much everything else, so you should only really need to import
this.
"""

# NOTE  Package-level re-exports. In addition to being terrible pedantic and
#       annoying, this serves two purposes:
#
#       1.  Makes indirect references in the documentation generator work. This
#           _might_ be avoidable with enough effort put into the resolver, but
#           for the moment it is what it is.
#
#       2.  Makes PyLance happy (VSCode Python type checker). It doesn't like
#           import splats
#
#               Wildcard import from a library not allowed
#               Pylance(reportWildcardImportFromLibrary)
#
from splatlog.typings import (
    LevelValue,
    LevelName,
    Level,
    Verbosity,
    is_verbosity,
    as_verbosity,
    VerbosityLevel,
    VerbosityRange,
    VerbosityLevels,
    VerbosityLevelsCastable,
    StdioName,
    RichConsoleCastable,
    RichThemeCastable,
    NamedHandlerCast,
    KwdMapping,
    HandlerCastable,
    ConsoleHandlerCastable,
    JSONEncoderStyle,
    ExportHandlerCastable,
    JSONFormatterCastable,
    JSONEncoderCastable,
    FileHandlerMode,
    ExcInfo,
)
from splatlog import lib
from splatlog.levels import (
    CRITICAL,
    FATAL,
    ERROR,
    WARNING,
    WARN,
    INFO,
    DEBUG,
    NOTSET,
    get_level_value,
    is_level_name,
    is_level_value,
    is_level,
)
from splatlog.names import (
    root_name,
    is_in_hierarchy,
)
from splatlog.verbosity import (
    VerbosityLevelResolver,
    VerbosityLevelsFilter,
    cast_verbosity_levels,
    get_verbosity_levels,
    set_verbosity_levels,
    del_verbosity_levels,
    get_verbosity,
    set_verbosity,
    del_verbosity,
)
from splatlog.locking import (
    lock,
)
from splatlog.splat_logger import (
    get_logger,
    getLogger,
    get_logger_for,
    LoggerProperty,
    SplatLogger,
    ClassLogger,
    SelfLogger,
)
from splatlog.rich_handler import (
    RichHandler,
)
from splatlog.json import (
    JSONEncoder,
    LOCAL_TIMEZONE,
    JSONFormatterCastable,
    JSONFormatter,
)
from splatlog.named_handlers import (
    register_named_handler,
    get_named_handler_cast,
    named_handler,
    get_named_handler,
    set_named_handler,
    cast_console_handler,
    cast_export_handler,
)
from splatlog.setup import (
    setup,
)
