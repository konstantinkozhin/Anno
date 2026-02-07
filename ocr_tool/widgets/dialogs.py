"""
Simple reusable dialogs — themed.
"""
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLineEdit, QPushButton, QSpinBox,
)
from PyQt6.QtCore import Qt

from ..theme import Styles


class LineEditDialog(QDialog):
    """Single-line text input dialog."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор")
        self.setFixedHeight(70)
        self.setMinimumWidth(420)
        self.setStyleSheet(Styles.dialog())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._edit = QLineEdit(text)
        self._edit.returnPressed.connect(self.accept)
        layout.addWidget(self._edit, 1)

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(Styles.button_primary())
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedWidth(70)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self._edit.setFocus()
        self._edit.selectAll()

    def get_text(self) -> str:
        return self._edit.text()


class PageJumpDialog(QDialog):
    """Minimal page navigation dialog — just a spin box and OK."""

    def __init__(self, current: int, total: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Перейти к странице")
        self.setFixedHeight(60)
        self.setMinimumWidth(200)
        self.setStyleSheet(Styles.dialog())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self._spin = QSpinBox()
        self._spin.setRange(1, total)
        self._spin.setValue(current)
        self._spin.setStyleSheet(Styles.spin_box())
        self._spin.setFixedWidth(80)
        self._spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._spin)

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(Styles.button_primary())
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedWidth(60)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self._spin.setFocus()
        self._spin.selectAll()

    def get_value(self) -> int:
        return self._spin.value()
