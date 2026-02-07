"""
Panels: FreeLinesPanel, FreeWordsPanel, StructurePanel.
"""
from typing import List, Optional

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

from ..theme import Styles
from .base import StructurePanelMixin
from .flow_layout import FlowLayout
from .chips import WordChip
from .containers import LineWidget, BlockWidget


# ======================================================================
#  FreeLinesPanel
# ======================================================================

class FreeLinesPanel(StructurePanelMixin, QFrame):
    """Drop zone for lines not assigned to any block."""

    line_clicked = pyqtSignal(int)
    line_ctrl_clicked = pyqtSignal(int)
    word_clicked = pyqtSignal(int)
    word_double_clicked = pyqtSignal(int)
    word_ctrl_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._default_style = Styles.free_lines_panel()
        self.setStyleSheet(self._default_style)
        self.setAcceptDrops(True)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(6)

    def add_line_widget(self, line_widget: LineWidget):
        line_widget.line_clicked.connect(self.line_clicked.emit)
        line_widget.line_ctrl_clicked.connect(self.line_ctrl_clicked.emit)
        line_widget.word_clicked.connect(self.word_clicked.emit)
        line_widget.word_double_clicked.connect(self.word_double_clicked.emit)
        line_widget.word_ctrl_clicked.connect(self.word_ctrl_clicked.emit)
        self._layout.addWidget(line_widget)

        panel = self._find_structure_panel()
        if panel:
            panel._widgets_map[("line", line_widget.line_id)] = line_widget

    # -- Drag-drop --

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("line:") or t.startswith("lines:"):
                event.acceptProposedAction()
                self.setStyleSheet(Styles.free_lines_panel_drop())

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event):
        self.setStyleSheet(self._default_style)
        try:
            text = event.mimeData().text()
            panel = self._find_structure_panel()
            if text.startswith("lines:") and panel:
                ids = [int(x) for x in text.split(":")[1].split(",") if x]
                panel.lines_dropped_to_free.emit(ids)
                event.acceptProposedAction()
            elif text.startswith("line:") and panel:
                panel.line_dropped_to_free.emit(int(text.split(":")[1]))
                event.acceptProposedAction()
        except Exception as e:
            print(f"[FreeLinesPanel] drop error: {e}")


# ======================================================================
#  FreeWordsPanel
# ======================================================================

class FreeWordsPanel(StructurePanelMixin, QFrame):
    """Mosaic panel for free (unassigned) words."""

    word_clicked = pyqtSignal(int)
    word_double_clicked = pyqtSignal(int)
    word_ctrl_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._default_style = Styles.free_words_panel()
        self.setStyleSheet(self._default_style)
        self.setAcceptDrops(True)
        self._layout = FlowLayout(self, margin=10, spacing=6)

    def add_word(self, box_id: int, text: str):
        chip = WordChip(box_id, text)
        chip.clicked.connect(self.word_clicked.emit)
        chip.double_clicked.connect(self.word_double_clicked.emit)
        chip.ctrl_clicked.connect(self.word_ctrl_clicked.emit)
        self._layout.addWidget(chip)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("word:") or t.startswith("words:"):
                event.acceptProposedAction()
                self.setStyleSheet(Styles.free_words_panel_drop())

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._default_style)

    def dropEvent(self, event):
        self.setStyleSheet(self._default_style)
        try:
            text = event.mimeData().text()
            panel = self._find_structure_panel()
            if text.startswith("words:") and panel:
                ids = [int(x) for x in text.split(":")[1].split(",") if x]
                panel.words_dropped_to_free.emit(ids)
                event.acceptProposedAction()
            elif text.startswith("word:") and panel:
                panel.word_dropped_to_free.emit(int(text.split(":")[1]))
                event.acceptProposedAction()
        except Exception as e:
            print(f"[FreeWordsPanel] drop error: {e}")


# ======================================================================
#  StructurePanel  (the big orchestrator on the right side)
# ======================================================================

class StructurePanel(QScrollArea):
    """Scrollable panel showing the hierarchical document structure."""

    _is_structure_panel = True  # marker for StructurePanelMixin

    # Selection signals
    block_clicked = pyqtSignal(int)
    block_double_clicked = pyqtSignal(int)
    line_clicked = pyqtSignal(int)
    line_ctrl_clicked = pyqtSignal(int)
    word_clicked = pyqtSignal(int)
    word_double_clicked = pyqtSignal(int)
    word_ctrl_clicked = pyqtSignal(int)
    empty_area_clicked = pyqtSignal()

    # Drag-drop signals  (forwarded from children)
    word_dropped_on_line = pyqtSignal(int, int, int)      # box_id, line_id, pos
    words_dropped_on_line = pyqtSignal(list, int, int)     # box_ids, line_id, pos
    word_dropped_to_free = pyqtSignal(int)
    words_dropped_to_free = pyqtSignal(list)
    line_dropped_on_block = pyqtSignal(int, int)           # line_id, block_id
    line_dropped_on_block_at_pos = pyqtSignal(int, int, int)
    lines_dropped_on_block = pyqtSignal(list, int)
    line_dropped_to_free = pyqtSignal(int)
    lines_dropped_to_free = pyqtSignal(list)
    line_reorder = pyqtSignal(int, int, int)               # line_id, block_id, new_pos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(Styles.structure_scroll())

        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(14, 14, 14, 14)
        self.main_layout.setSpacing(10)
        self.main_layout.addStretch()
        self.setWidget(self.container)

        self._widgets_map: dict = {}
        self.free_words_panel: Optional[FreeWordsPanel] = None
        self.free_lines_panel: Optional[FreeLinesPanel] = None
        self.multi_selected_ids: List[int] = []
        self.multi_selected_line_ids: List[int] = []

        self.container.mousePressEvent = self._on_container_clicked

    # -- Container click --

    def _on_container_clicked(self, event):
        self._clear_all_selections()
        self.empty_area_clicked.emit()

    # -- Clear / rebuild helpers --

    def clear(self):
        while self.main_layout.count() > 1:
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._widgets_map.clear()
        self.free_words_panel = None
        self.free_lines_panel = None

    # -- Add widgets --

    def add_block(self, block_id: int, name: str) -> BlockWidget:
        block = BlockWidget(block_id, name)
        block.block_clicked.connect(self.block_clicked.emit)
        block.block_double_clicked.connect(self.block_double_clicked.emit)
        block.line_clicked.connect(self.line_clicked.emit)
        block.line_ctrl_clicked.connect(self.toggle_line_multi_selection)
        block.word_clicked.connect(self.word_clicked.emit)
        block.word_double_clicked.connect(self.word_double_clicked.emit)
        block.word_ctrl_clicked.connect(self.toggle_multi_selection)
        self.main_layout.insertWidget(self.main_layout.count() - 1, block)
        self._widgets_map[("block", block_id)] = block
        return block

    def add_line(self, line_id: int, text: str) -> LineWidget:
        line = LineWidget(line_id, text)
        line.line_clicked.connect(self.line_clicked.emit)
        line.line_ctrl_clicked.connect(self.toggle_line_multi_selection)
        line.word_clicked.connect(self.word_clicked.emit)
        line.word_double_clicked.connect(self.word_double_clicked.emit)
        line.word_ctrl_clicked.connect(self.toggle_multi_selection)
        self.main_layout.insertWidget(self.main_layout.count() - 1, line)
        self._widgets_map[("line", line_id)] = line
        return line

    def add_section_header(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(Styles.section_header())
        self.main_layout.insertWidget(self.main_layout.count() - 1, lbl)

    def add_free_words_panel(self) -> FreeWordsPanel:
        self.free_words_panel = FreeWordsPanel()
        self.free_words_panel.word_clicked.connect(self.word_clicked.emit)
        self.free_words_panel.word_double_clicked.connect(self.word_double_clicked.emit)
        self.free_words_panel.word_ctrl_clicked.connect(self.toggle_multi_selection)
        self.main_layout.insertWidget(self.main_layout.count() - 1, self.free_words_panel)
        return self.free_words_panel

    def add_free_lines_panel(self) -> FreeLinesPanel:
        self.free_lines_panel = FreeLinesPanel()
        self.free_lines_panel.line_clicked.connect(self.line_clicked.emit)
        self.free_lines_panel.line_ctrl_clicked.connect(self.toggle_line_multi_selection)
        self.free_lines_panel.word_clicked.connect(self.word_clicked.emit)
        self.free_lines_panel.word_double_clicked.connect(self.word_double_clicked.emit)
        self.free_lines_panel.word_ctrl_clicked.connect(self.toggle_multi_selection)
        self.main_layout.insertWidget(self.main_layout.count() - 1, self.free_lines_panel)
        return self.free_lines_panel

    # -- Selection management --

    def select_item(self, item_type: str, item_id: int):
        self._clear_all_selections()
        if item_type == "box":
            chip = self._find_word_chip(item_id)
            if chip:
                chip.setSelected(True)
                self.ensureWidgetVisible(chip)
        elif item_type in ("block", "line"):
            key = (item_type, item_id)
            if key in self._widgets_map:
                w = self._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(True)
                self.ensureWidgetVisible(w)

    def _clear_all_selections(self):
        self.multi_selected_ids.clear()
        self.multi_selected_line_ids.clear()
        for key, widget in list(self._widgets_map.items()):
            try:
                if hasattr(widget, "setSelected"):
                    widget.setSelected(False)
                if hasattr(widget, "findChildren"):
                    for chip in widget.findChildren(WordChip):
                        chip.setSelected(False)
            except RuntimeError:
                pass
        for panel in (self.free_words_panel, self.free_lines_panel):
            if panel:
                try:
                    for chip in panel.findChildren(WordChip):
                        chip.setSelected(False)
                except RuntimeError:
                    pass

    def _find_word_chip(self, box_id: int) -> Optional[WordChip]:
        for widget in list(self._widgets_map.values()):
            try:
                for chip in widget.findChildren(WordChip):
                    if chip.box_id == box_id:
                        return chip
            except RuntimeError:
                pass
        for panel in (self.free_words_panel, self.free_lines_panel):
            if panel:
                try:
                    for chip in panel.findChildren(WordChip):
                        if chip.box_id == box_id:
                            return chip
                except RuntimeError:
                    pass
        return None

    # -- Multi-selection (Ctrl+click) --

    def set_multi_selection(self, box_ids: list):
        for bid in self.multi_selected_ids:
            chip = self._find_word_chip(bid)
            if chip:
                chip.setSelected(False)
        self.multi_selected_ids = box_ids.copy()
        for bid in box_ids:
            chip = self._find_word_chip(bid)
            if chip:
                chip.setSelected(True)

    def toggle_multi_selection(self, box_id: int):
        chip = self._find_word_chip(box_id)
        if box_id in self.multi_selected_ids:
            self.multi_selected_ids.remove(box_id)
            if chip:
                chip.setSelected(False)
        else:
            self.multi_selected_ids.append(box_id)
            if chip:
                chip.setSelected(True)
        self.word_ctrl_clicked.emit(box_id)

    def set_line_multi_selection(self, line_ids: list):
        for lid in self.multi_selected_line_ids:
            key = ("line", lid)
            if key in self._widgets_map:
                w = self._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(False)
        self.multi_selected_line_ids = line_ids.copy()
        for lid in line_ids:
            key = ("line", lid)
            if key in self._widgets_map:
                w = self._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(True)

    def toggle_line_multi_selection(self, line_id: int):
        key = ("line", line_id)
        if line_id in self.multi_selected_line_ids:
            self.multi_selected_line_ids.remove(line_id)
            if key in self._widgets_map:
                w = self._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(False)
        else:
            self.multi_selected_line_ids.append(line_id)
            if key in self._widgets_map:
                w = self._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(True)
        self.line_ctrl_clicked.emit(line_id)
