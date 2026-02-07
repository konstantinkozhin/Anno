"""
Base classes, mixins and small reusable widgets shared across the package.
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from ..theme import Styles


# ----------------------------------------------------------------------
#  Drag-drop MIME protocol constants
# ----------------------------------------------------------------------

class DragTypes:
    """String prefixes used in QMimeData for internal drag-and-drop."""
    WORD = "word"        # single word  → "word:<id>"
    WORDS = "words"      # multi-word   → "words:<id>,<id>,…"
    LINE = "line"        # single line  → "line:<id>"
    LINES = "lines"      # multi-line   → "lines:<id>,<id>,…"
    BLOCK = "block"      # single block → "block:<id>"


# ----------------------------------------------------------------------
#  Mixin: find StructurePanel ancestor
# ----------------------------------------------------------------------

class StructurePanelMixin:
    """Mixin that adds ``_find_structure_panel()`` via duck-typing.

    Any ancestor widget that has ``_is_structure_panel = True``
    (set on *StructurePanel*) will be returned.  This avoids
    circular imports.
    """

    def _find_structure_panel(self):
        parent = self.parent()
        for _ in range(20):
            if parent is None:
                return None
            if getattr(parent, "_is_structure_panel", False):
                return parent
            parent = parent.parent()
        return None


# ----------------------------------------------------------------------
#  DragGrip: tiny drag handle ("⋮⋮")
# ----------------------------------------------------------------------

class DragGrip(QLabel):
    """Small drag-handle indicator."""

    def __init__(self, parent=None):
        super().__init__("⋮⋮", parent)
        self.setFixedWidth(20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(Styles.drag_grip())
        self.setCursor(Qt.CursorShape.OpenHandCursor)
