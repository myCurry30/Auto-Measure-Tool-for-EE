"""Application package containing main window and state management."""
from .state import AppState
from .theme import apply_theme, LIGHT_STYLE, DARK_STYLE

__all__ = ['AppState', 'apply_theme', 'LIGHT_STYLE', 'DARK_STYLE']