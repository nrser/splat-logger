from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

THEME = Theme(
    {
        "log.level": "bold",
        "log.name": "dim blue",
        "log.label": "dim white",
        "log.data.name": "italic blue",
        "log.data.type": "italic #4ec9b0",
    }
)

DEFAULT_CONSOLE = Console(theme=THEME)
