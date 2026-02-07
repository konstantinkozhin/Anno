"""
WordChip — draggable word "brick" widget.
"""
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QDrag, QMouseEvent
from PyQt6 import sip

from ..theme import Styles
from .base import DragGrip, StructurePanelMixin


class WordChip(StructurePanelMixin, QFrame):
    """Visual 'chip' for a single word (box)."""

    clicked = pyqtSignal(int)         # box_id
    double_clicked = pyqtSignal(int)  # box_id
    ctrl_clicked = pyqtSignal(int)    # box_id  (Ctrl+click for multi-select)

    def __init__(self, box_id: int, text: str, draggable: bool = True, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self._selected = False
        self._draggable = draggable
        self._drag_start_pos = None
        self._was_dragged = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)

        if draggable:
            self.grip = DragGrip()
            layout.addWidget(self.grip)

        self.label = QLabel(text if text else "[?]")
        self.label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.label)

        self._apply_style()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"ID: {box_id}\nДвойной клик = редактировать")

    # -- Selection --

    def setSelected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            Styles.word_chip_selected() if self._selected else Styles.word_chip_normal()
        )

    # -- Mouse events --

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.ctrl_clicked.emit(self.box_id)
            self._drag_start_pos = None
            self._was_dragged = False
        else:
            self._drag_start_pos = event.pos()
            self._was_dragged = False
            panel = self._find_structure_panel()
            if not (panel and self.box_id in panel.multi_selected_ids):
                self.clicked.emit(self.box_id)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._was_dragged and self._drag_start_pos is not None:
                panel = self._find_structure_panel()
                if panel and self.box_id in panel.multi_selected_ids:
                    self.clicked.emit(self.box_id)
            self._drag_start_pos = None
            self._was_dragged = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.box_id)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self._draggable or not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return

        self._was_dragged = True
        try:
            if sip.isdeleted(self):
                return

            drag = QDrag(self)
            mime = self._build_mime_data()
            pixmap = self._build_drag_pixmap()

            drag.setMimeData(mime)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(10, pixmap.height() // 2))

            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            drag.exec(Qt.DropAction.MoveAction)

            if not sip.isdeleted(self):
                self.setCursor(Qt.CursorShape.PointingHandCursor)
        except RuntimeError:
            pass
        except Exception as e:
            print(f"[WordChip] drag error: {e}")
        finally:
            self._drag_start_pos = None

    # -- Drag helpers --

    def _build_mime_data(self):
        from PyQt6.QtCore import QMimeData

        mime = QMimeData()
        panel = self._find_structure_panel()
        if panel and self.box_id in panel.multi_selected_ids:
            ids_str = ",".join(str(bid) for bid in panel.multi_selected_ids)
            mime.setText(f"words:{ids_str}")
        else:
            mime.setText(f"word:{self.box_id}")
        return mime

    def _build_drag_pixmap(self) -> QPixmap:
        panel = self._find_structure_panel()
        if panel and self.box_id in panel.multi_selected_ids:
            return self._composite_pixmap(panel)
        return self.grab()

    def _composite_pixmap(self, panel) -> QPixmap:
        """Composite pixmap of all multi-selected words side-by-side."""
        chips = []
        for bid in panel.multi_selected_ids:
            chip = panel._find_word_chip(bid)
            if chip:
                chips.append(chip.grab())
        if not chips:
            return self.grab()

        total_w = sum(p.width() for p in chips)
        max_h = max(p.height() for p in chips)
        composite = QPixmap(total_w, max_h)
        composite.fill(Qt.GlobalColor.transparent)

        painter = QPainter(composite)
        x = 0
        for p in chips:
            painter.drawPixmap(x, (max_h - p.height()) // 2, p)
            x += p.width()
        painter.end()
        return composite
