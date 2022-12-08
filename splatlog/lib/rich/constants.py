from __future__ import annotations

from rich.console import Console
from rich.theme import Theme
from rich.style import Style

THEME = Theme(
    {
        "log.level": Style(bold=True),
        "log.name": Style(color="blue", dim=True),
        "log.name.sep": Style(color="white", dim=True),
        "log.class": Style(color="yellow", dim=True),
        "log.funcName": Style(color="cyan", dim=True),
        "log.label": Style(color="white", dim=True),
        "log.data.name": Style(color="blue", italic=True),
        "log.data.type": Style(color="#4ec9b0", italic=True),
    }
)

DEFAULT_CONSOLE = Console(theme=THEME)
