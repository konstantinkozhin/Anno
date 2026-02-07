"""
OCRApp — main window that wires all services and widgets together.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QSplitter,
    QScrollArea, QDialog,
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QKeyEvent

from .theme import Styles, init_theme, set_dark, is_dark
from .models import Box, Line, Block, OCRDatabase
from .widgets.viewer import ImageViewer
from .widgets.panels import StructurePanel
from .widgets.containers import LineWidget
from .widgets.dialogs import LineEditDialog, PageJumpDialog
from .services.export import ExportService


class OCRApp(QMainWindow):
    """Top-level application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Tool v3.0")
        self.resize(1400, 900)
        self.setStyleSheet(Styles.main_window())

        self.db: Optional[OCRDatabase] = None
        self.image_folder: Optional[str] = None
        self.images_list: List[str] = []
        self.current_image_idx = -1
        self.selected_item = None  # ('block'|'line'|'box', id)

        self._init_ui()

    # ==================================================================
    #  UI construction
    # ==================================================================

    def _init_ui(self):
        # ---- Menu bar ----
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        act_open = file_menu.addAction("Открыть папку")
        act_open.triggered.connect(self.open_folder)
        act_open.setShortcut("Ctrl+O")

        file_menu.addSeparator()
        file_menu.addAction(
            "Экспорт датасета (JSON)"
        ).triggered.connect(self._export_json)
        file_menu.addAction(
            "Импорт датасета (JSON)"
        ).triggered.connect(self._import_json)
        file_menu.addSeparator()
        file_menu.addAction(
            "Экспорт COCO (JSON)"
        ).triggered.connect(self._export_coco)
        file_menu.addAction(
            "Импорт COCO (JSON)"
        ).triggered.connect(self._import_coco)
        file_menu.addSeparator()

        act_exit = file_menu.addAction("Выход")
        act_exit.triggered.connect(self.close)
        act_exit.setShortcut("Ctrl+Q")

        view_menu = menubar.addMenu("Тема")
        self._act_theme = view_menu.addAction("Сменить тему")
        self._act_theme.setCheckable(True)
        self._act_theme.setChecked(is_dark())
        self._act_theme.triggered.connect(self._toggle_theme)

        help_menu = menubar.addMenu("Справка")
        help_menu.addAction("Горячие клавиши").triggered.connect(
            self._show_help
        )

        # ---- Central widget ----
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central)

        # -- Top bar (full width above canvas + panel) --
        self._status_bar = self._build_status_bar()
        main_layout.addWidget(self._status_bar)

        # -- Viewer --
        self.viewer = ImageViewer()
        self.viewer.zoom_changed.connect(self._update_zoom_label)
        self.viewer.box_changed.connect(self._on_box_changed)
        self.viewer.box_selected.connect(self._on_canvas_box_selected)
        self.viewer.selection_cleared.connect(
            self._on_canvas_selection_cleared
        )
        self.viewer.multi_selection_changed.connect(
            self._on_multi_selection_changed
        )

        self._viewer_scroll = QScrollArea()
        self._viewer_scroll.setWidget(self.viewer)
        self._viewer_scroll.setWidgetResizable(True)
        self._viewer_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._viewer_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._viewer_scroll.setStyleSheet(Styles.viewer_scroll())

        # -- Right (structure) --
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.structure_panel = StructurePanel()
        self._connect_structure_signals()
        right.addWidget(self.structure_panel)

        btns = self._build_action_buttons()
        right.addLayout(btns)

        # -- Splitter (canvas left, structure right) --
        self._splitter = QSplitter()
        self._splitter.setStyleSheet(Styles.splitter())
        self._splitter.addWidget(self._viewer_scroll)
        w_r = QWidget()
        w_r.setLayout(right)
        self._splitter.addWidget(w_r)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([3000, 1000])
        main_layout.addWidget(self._splitter)

        # Blink timer
        self._blink_timer = QTimer()
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start(400)

        self._update_nav_buttons()

    # -- helpers used by _init_ui --

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)
        bar.setFixedHeight(48)
        bar.setStyleSheet(Styles.status_bar_container())

        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet(Styles.filename_label())
        self.lbl_filename.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_filename.setToolTip("Клик: копировать имя файла")
        self.lbl_filename.mousePressEvent = self._on_filename_clicked
        lay.addWidget(self.lbl_filename)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedSize(32, 28)
        self.btn_prev.clicked.connect(self.go_prev)
        self.btn_prev.setStyleSheet(Styles.nav_button())
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.btn_prev)

        self.lbl_page = QLabel("")
        self.lbl_page.setStyleSheet(Styles.page_label())
        self.lbl_page.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_page.setToolTip("Клик: перейти к странице")
        self.lbl_page.mousePressEvent = self._on_page_clicked
        lay.addWidget(self.lbl_page)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedSize(32, 28)
        self.btn_next.clicked.connect(self.go_next)
        self.btn_next.setStyleSheet(Styles.nav_button())
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.btn_next)

        self.lbl_status = QLabel("Откройте папку (Ctrl+O)")
        self.lbl_status.setStyleSheet(Styles.status_label())
        lay.addWidget(self.lbl_status, 1)

        # -- Display toggle buttons --
        self._btn_dim = QPushButton("Затенение")
        self._btn_dim.setCheckable(True)
        self._btn_dim.setChecked(False)
        self._btn_dim.setStyleSheet(Styles.toggle_button())
        self._btn_dim.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_dim.setToolTip("Затенить область вне боксов")
        self._btn_dim.toggled.connect(self._toggle_dim)
        lay.addWidget(self._btn_dim)

        self._btn_labels = QPushButton("Aa Текст")
        self._btn_labels.setCheckable(True)
        self._btn_labels.setChecked(True)
        self._btn_labels.setStyleSheet(Styles.toggle_button())
        self._btn_labels.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_labels.setToolTip("Показать/скрыть расшифровки на холсте")
        self._btn_labels.toggled.connect(self._toggle_labels)
        lay.addWidget(self._btn_labels)

        self._zoom_buttons: list = []
        for text, slot in [
            ("−", lambda: self.viewer.adjust_zoom(0.8)),
            ("+", lambda: self.viewer.adjust_zoom(1.2)),
            ("↻", lambda: self.viewer.reset_zoom()),
        ]:
            b = QPushButton(text)
            b.setFixedSize(26, 26)
            b.clicked.connect(slot)
            b.setStyleSheet(Styles.zoom_button())
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            lay.addWidget(b)
            self._zoom_buttons.append(b)
            if text == "−":
                self.lbl_zoom = QLabel("100%")
                self.lbl_zoom.setFixedWidth(50)
                self.lbl_zoom.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                self.lbl_zoom.setStyleSheet(Styles.zoom_label())
                lay.addWidget(self.lbl_zoom)

        return bar

    def _build_action_buttons(self) -> QHBoxLayout:
        lay = QHBoxLayout()
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        btn_block = QPushButton("+ Блок")
        btn_block.clicked.connect(self._add_block)
        btn_block.setStyleSheet(Styles.button())
        btn_block.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn_block)

        btn_line = QPushButton("+ Строка")
        btn_line.clicked.connect(self._add_empty_line)
        btn_line.setStyleSheet(Styles.button())
        btn_line.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(btn_line)

        self._btn_delete = QPushButton("Удалить")
        self._btn_delete.clicked.connect(self._delete_selected)
        self._btn_delete.setStyleSheet(Styles.button_danger())
        self._btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self._btn_delete)

        lay.addStretch()
        return lay

    def _connect_structure_signals(self):
        sp = self.structure_panel
        sp.block_clicked.connect(self._on_block_clicked)
        sp.block_double_clicked.connect(self._on_block_dbl_clicked)
        sp.line_clicked.connect(self._on_line_clicked)
        sp.word_clicked.connect(self._on_word_clicked)
        sp.word_double_clicked.connect(self._on_word_dbl_clicked)
        sp.word_dropped_on_line.connect(self._on_word_dropped_on_line)
        sp.words_dropped_on_line.connect(self._on_words_dropped_on_line)
        sp.word_dropped_to_free.connect(self._on_word_dropped_to_free)
        sp.words_dropped_to_free.connect(self._on_words_dropped_to_free)
        sp.line_dropped_on_block.connect(self._on_line_dropped_on_block)
        sp.lines_dropped_on_block.connect(self._on_lines_dropped_on_block)
        sp.line_dropped_on_block_at_pos.connect(
            self._on_line_dropped_on_block_at_pos
        )
        sp.line_dropped_to_free.connect(self._on_line_dropped_to_free)
        sp.lines_dropped_to_free.connect(self._on_lines_dropped_to_free)
        sp.line_reorder.connect(self._on_line_reorder)
        sp.word_ctrl_clicked.connect(self._on_panel_word_ctrl)
        sp.line_ctrl_clicked.connect(self._on_panel_line_ctrl)
        sp.empty_area_clicked.connect(self._on_panel_empty)

    # ==================================================================
    #  Theme toggle
    # ==================================================================

    def _toggle_theme(self, checked: bool):
        set_dark(checked)
        self._act_theme.setChecked(checked)
        QApplication.instance().setStyleSheet(Styles.global_app())
        self._apply_theme()

    # ==================================================================
    #  Display toggles
    # ==================================================================

    def _toggle_dim(self, checked: bool):
        self.viewer.dim_non_boxes = checked
        self.viewer.update()

    def _toggle_labels(self, checked: bool):
        self.viewer.show_labels = checked
        self.viewer.update()

    def _apply_theme(self):
        """Re-apply theme to all UI elements after a palette switch."""
        self.setStyleSheet(Styles.main_window())
        self._status_bar.setStyleSheet(Styles.status_bar_container())
        self.lbl_filename.setStyleSheet(Styles.filename_label())
        self.lbl_page.setStyleSheet(Styles.page_label())
        self.lbl_status.setStyleSheet(Styles.status_label())
        self.lbl_zoom.setStyleSheet(Styles.zoom_label())
        self.btn_prev.setStyleSheet(Styles.nav_button())
        self.btn_next.setStyleSheet(Styles.nav_button())
        for b in self._zoom_buttons:
            b.setStyleSheet(Styles.zoom_button())
        self._viewer_scroll.setStyleSheet(Styles.viewer_scroll())
        self._splitter.setStyleSheet(Styles.splitter())
        self._btn_delete.setStyleSheet(Styles.button_danger())
        self._btn_dim.setStyleSheet(Styles.toggle_button())
        self._btn_labels.setStyleSheet(Styles.toggle_button())
        self.structure_panel.setStyleSheet(Styles.structure_scroll())
        # Rebuild structure panel (re-styles all children)
        if self.current_image_idx >= 0:
            self._load_image(preserve_view=True)
        self.viewer.update()

    # ==================================================================
    #  Folder / Image loading
    # ==================================================================

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Выберите папку с изображениями"
        )
        if not path:
            return
        self.image_folder = path
        self.db = OCRDatabase(os.path.join(path, "annotations.db"))
        exts = {".jpg", ".jpeg", ".png", ".bmp"}
        self.images_list = sorted(
            f for f in os.listdir(path) if Path(f).suffix.lower() in exts
        )
        if not self.images_list:
            QMessageBox.warning(self, "Пусто", "Нет изображений.")
            return
        self.current_image_idx = 0
        self._load_image()

    def _load_image(self, preserve_view=False, preserve_selection=False):
        if not (0 <= self.current_image_idx < len(self.images_list)):
            return
        name = self.images_list[self.current_image_idx]

        # Guarantee unified hierarchy
        self.db.ensure_defaults(name)

        pix = QPixmap(os.path.join(self.image_folder, name))
        boxes = self.db.get_boxes(name)
        lines = self.db.get_lines(name)
        blocks = self.db.get_blocks(name)

        self.viewer.set_image(
            pix, boxes, lines, blocks, preserve_view=preserve_view
        )
        self._update_nav_buttons()

        # Count "placed" = not in default line
        default_line_ids = {ln.id for ln in lines if ln.is_default}
        in_lines = sum(
            1 for b in boxes if b.line_id not in default_line_ids
        )
        self.lbl_filename.setText(f"{name}")
        self.lbl_page.setText(
            f"[{self.current_image_idx + 1}/{len(self.images_list)}]"
        )
        self.lbl_status.setText(
            f"Боксов: {in_lines}/{len(boxes)} в строках | "
            f"Строк: {sum(1 for ln in lines if not ln.is_default)} | "
            f"Блоков: {sum(1 for b in blocks if not b.is_default)}"
        )
        self._rebuild_structure(boxes, lines, blocks, preserve_selection)

    # ==================================================================
    #  Structure panel rebuild
    # ==================================================================

    def _rebuild_structure(
        self,
        boxes: List[Box],
        lines: List[Line],
        blocks: List[Block],
        preserve_selection=False,
    ):
        saved_wids = (
            self.structure_panel.multi_selected_ids.copy()
            if preserve_selection
            else []
        )
        saved_lids = (
            self.structure_panel.multi_selected_line_ids.copy()
            if preserve_selection
            else []
        )

        self.structure_panel.clear()
        box_map = {b.id: b for b in boxes}
        line_map = {ln.id: ln for ln in lines}

        default_block = next((b for b in blocks if b.is_default), None)
        default_line = next((ln for ln in lines if ln.is_default), None)

        # ---- Regular blocks (non-default) ----
        for block in blocks:
            if block.is_default:
                continue
            bw = self.structure_panel.add_block(block.id, block.name)
            for lid in block.lines:
                ln = line_map.get(lid)
                if ln and not ln.is_default:
                    lw = LineWidget(ln.id, ln.text)
                    for bid in ln.boxes:
                        bx = box_map.get(bid)
                        if bx:
                            lw.add_word(bx.id, bx.text)
                    bw.add_line_widget(lw)

        # ---- Free lines (non-default lines inside default block) ----
        free_lines_in_default = []
        if default_block:
            for lid in default_block.lines:
                ln = line_map.get(lid)
                if ln and not ln.is_default:
                    free_lines_in_default.append(ln)

        has_blocks = sum(1 for b in blocks if not b.is_default)
        if free_lines_in_default or has_blocks:
            self.structure_panel.add_section_header(
                f"Без блока ({len(free_lines_in_default)})"
            )
            fl_panel = self.structure_panel.add_free_lines_panel()
            for ln in free_lines_in_default:
                lw = LineWidget(ln.id, ln.text)
                for bid in ln.boxes:
                    bx = box_map.get(bid)
                    if bx:
                        lw.add_word(bx.id, bx.text)
                fl_panel.add_line_widget(lw)

        # ---- Free words (boxes inside the default line) ----
        free_boxes = []
        if default_line:
            free_boxes = [
                box_map[bid]
                for bid in default_line.boxes
                if bid in box_map
            ]

        self.structure_panel.add_section_header(
            f"Свободные слова ({len(free_boxes)})"
        )
        fw_panel = self.structure_panel.add_free_words_panel()
        for bx in free_boxes:
            fw_panel.add_word(bx.id, bx.text)

        # Restore multi-selection
        if preserve_selection:
            existing_bids = {b.id for b in boxes}
            existing_lids = {ln.id for ln in lines}
            valid_w = [i for i in saved_wids if i in existing_bids]
            valid_l = [i for i in saved_lids if i in existing_lids]
            if valid_w:
                self.structure_panel.set_multi_selection(valid_w)
            if valid_l:
                self.structure_panel.set_line_multi_selection(valid_l)

    # ==================================================================
    #  Click handlers (block / line / word)
    # ==================================================================

    def _on_block_clicked(self, block_id):
        if self.viewer.current_block_id == block_id:
            self.viewer.current_block_id = None
            self.selected_item = None
            self.structure_panel._clear_all_selections()
            self.viewer.update()
            return
        self.selected_item = ("block", block_id)
        self.viewer.current_line_id = None
        self.viewer.current_block_id = block_id
        self.viewer.edit_box_id = None
        self.viewer.multi_selected_boxes = []
        self.structure_panel.select_item("block", block_id)
        self._center_on_block(block_id)
        self.viewer.update()

    def _on_block_dbl_clicked(self, block_id):
        blk = next(
            (
                b
                for b in self.db.get_blocks(
                    self.images_list[self.current_image_idx]
                )
                if b.id == block_id
            ),
            None,
        )
        if blk:
            dlg = LineEditDialog(blk.name, self)
            dlg.setWindowTitle("Название блока")
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.db.update_block_name(block_id, dlg.get_text())
                self._load_image(preserve_view=True)

    def _on_line_clicked(self, line_id):
        if self.viewer.current_line_id == line_id:
            self.viewer.current_line_id = None
            self.selected_item = None
            self.structure_panel._clear_all_selections()
            self.viewer.update()
            return
        self.selected_item = ("line", line_id)
        self.viewer.current_line_id = line_id
        self.viewer.current_block_id = None
        self.viewer.edit_box_id = None
        self.viewer.multi_selected_boxes = []
        self.structure_panel.select_item("line", line_id)
        self._center_on_line(line_id)
        self.viewer.update()

    def _on_word_clicked(self, box_id):
        if self.viewer.edit_box_id == box_id:
            self.viewer.edit_box_id = None
            self.selected_item = None
            self.structure_panel._clear_all_selections()
            self.viewer.update()
            return
        self.selected_item = ("box", box_id)
        self.viewer.edit_box_id = box_id
        self.viewer.current_line_id = None
        self.viewer.current_block_id = None
        self.viewer.multi_selected_boxes = []
        self.structure_panel.select_item("box", box_id)
        self._center_on_box(box_id)
        self.viewer.update()

    def _on_word_dbl_clicked(self, box_id):
        box = next((b for b in self.viewer.boxes if b.id == box_id), None)
        if box:
            dlg = LineEditDialog(box.text, self)
            dlg.setWindowTitle("Редактирование слова")
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.db.update_box_text(box_id, dlg.get_text())
                self._load_image(preserve_view=True)

    # ==================================================================
    #  Centering helpers
    # ==================================================================

    def _center_on_point(self, x_norm, y_norm):
        if not self.viewer.image:
            return
        wi, hi = self.viewer.image.width(), self.viewer.image.height()
        px, py = x_norm * wi, y_norm * hi
        s, _, _ = self.viewer.get_transform()
        ww, wh = self.viewer.width(), self.viewer.height()
        tx = ww / 2 - px * s - (ww - wi * s) / 2
        ty = wh / 2 - py * s - (wh - hi * s) / 2
        self.viewer.pan_pos = QPoint(int(tx), int(ty))

    def _center_on_box(self, box_id):
        b = next(
            (x for x in self.viewer.boxes if x.id == box_id), None
        )
        if b:
            self._center_on_point(b.x_center, b.y_center)

    def _center_on_line(self, line_id):
        ln = next(
            (x for x in self.viewer.lines if x.id == line_id), None
        )
        if ln and ln.boxes:
            bs = [
                b for b in self.viewer.boxes if b.id in ln.boxes
            ]
            if bs:
                self._center_on_point(
                    sum(b.x_center for b in bs) / len(bs),
                    sum(b.y_center for b in bs) / len(bs),
                )

    def _center_on_block(self, block_id):
        blk = next(
            (x for x in self.viewer.blocks if x.id == block_id), None
        )
        if not blk or not blk.lines:
            return
        bs = []
        for lid in blk.lines:
            ln = next(
                (x for x in self.viewer.lines if x.id == lid), None
            )
            if ln:
                bs.extend(
                    b for b in self.viewer.boxes if b.id in ln.boxes
                )
        if bs:
            self._center_on_point(
                sum(b.x_center for b in bs) / len(bs),
                sum(b.y_center for b in bs) / len(bs),
            )

    # ==================================================================
    #  Canvas ↔ Panel sync
    # ==================================================================

    def _on_canvas_box_selected(self, box_id):
        self.selected_item = ("box", box_id)
        self.structure_panel.select_item("box", box_id)

    def _on_canvas_selection_cleared(self):
        self.selected_item = None
        self.viewer.edit_box_id = None
        self.viewer.current_line_id = None
        self.viewer.current_block_id = None
        self.structure_panel._clear_all_selections()
        self.viewer.update()

    def _on_multi_selection_changed(self, ids):
        self.structure_panel.set_multi_selection(ids)

    def _on_panel_word_ctrl(self, box_id):
        if self.viewer.edit_box_id is not None:
            eid = self.viewer.edit_box_id
            if eid not in self.structure_panel.multi_selected_ids:
                self.structure_panel.multi_selected_ids.insert(0, eid)
                chip = self.structure_panel._find_word_chip(eid)
                if chip:
                    chip.setSelected(True)
            self.viewer.edit_box_id = None
        self.viewer.multi_selected_boxes = (
            self.structure_panel.multi_selected_ids.copy()
        )
        self.viewer.update()

    def _on_panel_line_ctrl(self, line_id):
        if self.viewer.current_line_id is not None:
            clid = self.viewer.current_line_id
            if clid not in self.structure_panel.multi_selected_line_ids:
                self.structure_panel.multi_selected_line_ids.insert(
                    0, clid
                )
                key = ("line", clid)
                if key in self.structure_panel._widgets_map:
                    w = self.structure_panel._widgets_map[key]
                    if hasattr(w, "setSelected"):
                        w.setSelected(True)
            self.viewer.current_line_id = None
        for lid in self.structure_panel.multi_selected_line_ids:
            key = ("line", lid)
            if key in self.structure_panel._widgets_map:
                w = self.structure_panel._widgets_map[key]
                if hasattr(w, "setSelected"):
                    w.setSelected(True)
        self.viewer.update()

    def _on_panel_empty(self):
        self.selected_item = None
        self.viewer.edit_box_id = None
        self.viewer.current_line_id = None
        self.viewer.current_block_id = None
        self.viewer.multi_selected_boxes = []
        self.viewer.update()

    # ==================================================================
    #  Drag-drop handlers
    # ==================================================================

    def _on_word_dropped_on_line(self, box_id, line_id, pos):
        if not self.db or line_id < 0:
            return
        if pos >= 0:
            self.db.move_box_to_line(box_id, line_id, order=pos)
            self._reorder_boxes(line_id, box_id, pos)
        else:
            self.db.move_box_to_line(box_id, line_id)
        self._clear_multi()
        self._load_image(preserve_view=True)

    def _on_words_dropped_on_line(self, box_ids, line_id, pos):
        if not self.db:
            return
        for i, bid in enumerate(box_ids):
            self.db.move_box_to_line(bid, line_id)
            name = self.images_list[self.current_image_idx]
            self.viewer.lines = self.db.get_lines(name)
            self._reorder_boxes(line_id, bid, pos + i)
        self._clear_multi()
        self._load_image(preserve_view=True)

    def _on_word_dropped_to_free(self, box_id):
        if self.db:
            self.db.move_box_to_line(box_id, None)  # → default line
            self._clear_multi()
            self._load_image(preserve_view=True)

    def _on_words_dropped_to_free(self, box_ids):
        if self.db:
            for bid in box_ids:
                self.db.move_box_to_line(bid, None)
            self._clear_multi()
            self._load_image(preserve_view=True)

    def _on_line_dropped_on_block(self, line_id, block_id):
        if self.db:
            self.db.move_line_to_block(line_id, block_id)
            self._load_image(preserve_view=True)

    def _on_lines_dropped_on_block(self, line_ids, block_id):
        if self.db:
            for lid in line_ids:
                self.db.move_line_to_block(lid, block_id)
            self.structure_panel.multi_selected_line_ids = []
            self._load_image(preserve_view=True)

    def _on_line_dropped_on_block_at_pos(self, line_id, block_id, pos):
        if self.db:
            self.db.move_line_to_block(line_id, block_id)
            self.db.reorder_line_in_block(line_id, block_id, pos)
            self._load_image(preserve_view=True)

    def _on_line_dropped_to_free(self, line_id):
        if self.db:
            self.db.move_line_to_block(line_id, None)  # → default block
            self.structure_panel.multi_selected_line_ids = []
            self._load_image(preserve_view=True)

    def _on_lines_dropped_to_free(self, line_ids):
        if self.db:
            for lid in line_ids:
                self.db.move_line_to_block(lid, None)
            self.structure_panel.multi_selected_line_ids = []
            self._load_image(preserve_view=True)

    def _on_line_reorder(self, line_id, block_id, new_pos):
        if self.db:
            self.db.reorder_line_in_block(line_id, block_id, new_pos)
            self._load_image(preserve_view=True)

    # -- helpers --

    def _reorder_boxes(self, line_id, inserted_bid, pos):
        ln = next(
            (x for x in self.viewer.lines if x.id == line_id), None
        )
        if not ln:
            return
        orig = (
            ln.boxes.index(inserted_bid)
            if inserted_bid in ln.boxes
            else -1
        )
        ids = [bid for bid in ln.boxes if bid != inserted_bid]
        adj = pos - 1 if 0 <= orig < pos else pos
        adj = max(0, min(adj, len(ids)))
        ids.insert(adj, inserted_bid)
        self.db.update_box_order_in_line(line_id, ids)

    def _clear_multi(self):
        self.viewer.multi_selected_boxes = []
        self.structure_panel.multi_selected_ids = []

    # ==================================================================
    #  Box editing (from canvas)
    # ==================================================================

    def _on_box_changed(self):
        if not self.db or self.current_image_idx < 0:
            return
        name = self.images_list[self.current_image_idx]
        if self.viewer.new_box_data:
            xc, yc, w, h = self.viewer.new_box_data
            new_id = self.db.create_box(name, xc, yc, w, h, "")
            self.viewer.new_box_data = None
            self._load_image(preserve_view=True)
            self.viewer.edit_box_id = new_id
            self.viewer.update()
            return
        if self.viewer.wants_text_edit:
            self.viewer.wants_text_edit = False
            self._edit_box_text()
            return
        if self.viewer.edit_box_id is not None:
            b = next(
                (
                    x
                    for x in self.viewer.boxes
                    if x.id == self.viewer.edit_box_id
                ),
                None,
            )
            if b:
                self.db.update_box(
                    b.id, b.x_center, b.y_center, b.width, b.height
                )

    def _edit_box_text(self):
        if self.viewer.edit_box_id is None:
            return
        box = next(
            (
                b
                for b in self.viewer.boxes
                if b.id == self.viewer.edit_box_id
            ),
            None,
        )
        if not box:
            return
        dlg = LineEditDialog(box.text, self)
        dlg.setWindowTitle("Редактирование расшифровки")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.db.update_box_text(box.id, dlg.get_text())
            self._load_image(preserve_view=True)

    # ==================================================================
    #  Navigation
    # ==================================================================

    def go_prev(self):
        if self.current_image_idx > 0:
            self.current_image_idx -= 1
            self._load_image()

    def go_next(self):
        if self.current_image_idx < len(self.images_list) - 1:
            self.current_image_idx += 1
            self._load_image()

    def _update_nav_buttons(self):
        has = len(self.images_list) > 0
        self.btn_prev.setEnabled(
            has and self.current_image_idx > 0
        )
        self.btn_next.setEnabled(
            has and self.current_image_idx < len(self.images_list) - 1
        )

    def _on_filename_clicked(self, event):
        if not self.images_list:
            return
        QApplication.clipboard().setText(
            self.images_list[self.current_image_idx]
        )
        self.lbl_filename.setStyleSheet(Styles.filename_label_copied())
        QTimer.singleShot(
            500,
            lambda: self.lbl_filename.setStyleSheet(
                Styles.filename_label()
            ),
        )

    def _on_page_clicked(self, event):
        if not self.images_list:
            return
        dlg = PageJumpDialog(
            self.current_image_idx + 1,
            len(self.images_list),
            self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.current_image_idx = dlg.get_value() - 1
            self._load_image()

    # ==================================================================
    #  Actions
    # ==================================================================

    def _add_block(self):
        if self.db and self.current_image_idx >= 0:
            self.db.create_block(
                self.images_list[self.current_image_idx]
            )
            self._load_image(
                preserve_view=True, preserve_selection=True
            )

    def _add_empty_line(self):
        if self.db and self.current_image_idx >= 0:
            self.db.create_line(
                self.images_list[self.current_image_idx], []
            )
            self._load_image(
                preserve_view=True, preserve_selection=True
            )

    def _delete_selected(self):
        if not self.selected_item:
            return
        t, i = self.selected_item
        if t == "block":
            self.db.delete_block(i)
        elif t == "line":
            self.db.delete_line(i)
        elif t == "box":
            self.db.delete_box(i)
        self.selected_item = None
        self.viewer.current_block_id = None
        self.viewer.current_line_id = None
        self.viewer.edit_box_id = None
        self._load_image(preserve_view=True)

    def _toggle_blink(self):
        self.viewer.blink_visible = not self.viewer.blink_visible
        if (
            self.viewer.current_line_id is not None
            or self.viewer.current_block_id is not None
        ):
            self.viewer.update()

    def _update_zoom_label(self, pct):
        self.lbl_zoom.setText(f"{pct}%")

    # ==================================================================
    #  Keyboard
    # ==================================================================

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key.Key_Left:
            self.go_prev()
            return
        if key == Qt.Key.Key_Right:
            self.go_next()
            return

        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            sp = self.structure_panel
            if sp.multi_selected_line_ids:
                for lid in sp.multi_selected_line_ids:
                    self.db.delete_line(lid)
                sp.multi_selected_line_ids = []
                self.viewer.current_line_id = None
                self._load_image(preserve_view=True)
            elif (
                self.viewer.multi_selected_boxes
                or sp.multi_selected_ids
            ):
                ids = (
                    self.viewer.multi_selected_boxes
                    or sp.multi_selected_ids
                )
                for bid in ids:
                    self.db.delete_box(bid)
                self._clear_multi()
                self._load_image(preserve_view=True)
            elif self.selected_item:
                self._delete_selected()
            elif self.viewer.edit_box_id is not None:
                self.db.delete_box(self.viewer.edit_box_id)
                self.viewer.edit_box_id = None
                self._load_image(preserve_view=True)
            elif self.viewer.current_line_id is not None:
                self.db.delete_line(self.viewer.current_line_id)
                self.viewer.current_line_id = None
                self._load_image(preserve_view=True)
            return

        if key == Qt.Key.Key_Escape:
            if self.viewer.multi_selected_boxes:
                self.viewer.multi_selected_boxes = []
                self.viewer.update()
                self.structure_panel.set_multi_selection([])
            elif self.viewer.edit_box_id is not None:
                self.viewer.edit_box_id = None
                self.viewer.update()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.viewer.multi_selected_boxes:
                # Create a new line from multi-selected boxes
                name = self.images_list[self.current_image_idx]
                self.db.create_line(name, self.viewer.multi_selected_boxes)
                self.viewer.multi_selected_boxes = []
                self.structure_panel.set_multi_selection([])
                self._load_image(preserve_view=True)
            elif self.viewer.edit_box_id is not None:
                self._edit_box_text()
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            if (
                event.modifiers()
                & Qt.KeyboardModifier.ControlModifier
            ):
                self.viewer.adjust_zoom(1.2)
        elif key == Qt.Key.Key_Minus:
            if (
                event.modifiers()
                & Qt.KeyboardModifier.ControlModifier
            ):
                self.viewer.adjust_zoom(0.8)
        elif key == Qt.Key.Key_0:
            if (
                event.modifiers()
                & Qt.KeyboardModifier.ControlModifier
            ):
                self.viewer.reset_zoom()
        else:
            super().keyPressEvent(event)

    # ==================================================================
    #  Export / Import JSON
    # ==================================================================

    def _export_json(self):
        if not self.db or not self.images_list:
            QMessageBox.warning(
                self, "Ошибка", "Нет открытых изображений"
            )
            return
        default = (
            os.path.basename(self.image_folder) or "export"
        ) + ".json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить JSON", default, "JSON (*.json)"
        )
        if not path:
            return
        dataset = {
            name: ExportService.build_page(
                self.db, self.image_folder, name
            )
            for name in self.images_list
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        QMessageBox.information(
            self,
            "Успех",
            f"Экспортировано {len(self.images_list)} страниц → {path}",
        )

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть JSON", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            if not isinstance(dataset, dict):
                QMessageBox.critical(
                    self, "Ошибка", "JSON должен быть словарём."
                )
                return
            valid = sum(
                1
                for v in dataset.values()
                if isinstance(v, dict) and "blocks" in v
            )
            if valid == 0:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Не найдено страниц в корректном формате.",
                )
                return

            folder = QFileDialog.getExistingDirectory(
                self, "Папка с изображениями для датасета"
            )
            if not folder:
                return

            exts = {".jpg", ".jpeg", ".png", ".bmp"}
            folder_imgs = {
                f
                for f in os.listdir(folder)
                if Path(f).suffix.lower() in exts
            }
            matching = folder_imgs & set(dataset.keys())
            if not matching:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    "Ни одно изображение из JSON не найдено в папке.",
                )
                return

            db_path = os.path.join(folder, "annotations.db")
            msg = f"Найдено {len(matching)} изображений.\n"
            if os.path.exists(db_path):
                msg += "ВНИМАНИЕ: БД будет ЗАМЕНЕНА!\n"
            msg += "Импортировать?"
            if (
                QMessageBox.question(
                    self,
                    "Подтверждение",
                    msg,
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return

            if os.path.exists(db_path):
                os.remove(db_path)

            self.image_folder = folder
            self.db = OCRDatabase(db_path)
            self.images_list = sorted(folder_imgs)
            count = 0
            for img_name, page in dataset.items():
                if img_name in folder_imgs:
                    ExportService.import_page(
                        self.db, folder, img_name, page
                    )
                    count += 1
            if self.images_list:
                self.current_image_idx = 0
                self._load_image()
            QMessageBox.information(
                self, "Успех", f"Импортировано {count} страниц"
            )
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка JSON", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ==================================================================
    #  COCO Export / Import
    # ==================================================================

    def _export_coco(self):
        if not self.db or not self.images_list:
            QMessageBox.warning(
                self, "Ошибка", "Нет открытых изображений"
            )
            return
        default = (
            os.path.basename(self.image_folder) or "export"
        ) + "_coco.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить COCO JSON", default, "JSON (*.json)"
        )
        if not path:
            return
        coco = ExportService.build_coco(
            self.db, self.image_folder, self.images_list
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(coco, f, ensure_ascii=False, indent=2)
        QMessageBox.information(
            self,
            "Успех",
            f"Экспортировано {len(coco['images'])} изображений, "
            f"{len(coco['annotations'])} аннотаций \u2192 {path}",
        )

    def _import_coco(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть COCO JSON", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                coco_data = json.load(f)

            if not isinstance(coco_data, dict):
                QMessageBox.critical(
                    self, "Ошибка", "JSON должен быть словарём."
                )
                return

            images = coco_data.get("images", [])
            annotations = coco_data.get("annotations", [])
            if not images:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не найден массив 'images' в COCO JSON.",
                )
                return

            folder = QFileDialog.getExistingDirectory(
                self, "Папка с изображениями"
            )
            if not folder:
                return

            exts = {".jpg", ".jpeg", ".png", ".bmp"}
            folder_imgs = {
                f
                for f in os.listdir(folder)
                if Path(f).suffix.lower() in exts
            }
            coco_names = {img["file_name"] for img in images}
            matching = folder_imgs & coco_names
            if not matching:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Ни одно изображение из COCO JSON не найдено в папке.",
                )
                return

            db_path = os.path.join(folder, "annotations.db")
            msg = (
                f"Найдено {len(matching)} изображений, "
                f"{len(annotations)} аннотаций.\n"
            )
            if os.path.exists(db_path):
                msg += "ВНИМАНИЕ: БД будет ЗАМЕНЕНА!\n"
            msg += "Импортировать?"

            if (
                QMessageBox.question(
                    self, "Подтверждение", msg,
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )
                != QMessageBox.StandardButton.Yes
            ):
                return

            if os.path.exists(db_path):
                os.remove(db_path)

            self.image_folder = folder
            self.db = OCRDatabase(db_path)
            self.images_list = sorted(folder_imgs)

            imported = ExportService.import_coco(
                self.db, folder, coco_data, folder_imgs
            )

            if self.images_list:
                self.current_image_idx = 0
                self._load_image()
            QMessageBox.information(
                self, "Успех",
                f"Импортировано {imported} страниц"
            )
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Ошибка JSON", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ==================================================================
    #  Help
    # ==================================================================

    def _show_help(self):
        QMessageBox.information(
            self,
            "Справка",
            (
                "<b>Горячие клавиши:</b><br><br>"
                "<b>Ctrl+O</b> — Открыть папку<br>"
                "<b>Ctrl +/-/0</b> — Масштаб<br>"
                "<b>← →</b> — Страницы<br>"
                "<b>Ctrl+ЛКМ</b> — Множественное выделение<br>"
                "<b>Enter</b> — Создать строку из выделенных<br>"
                "<b>Esc</b> — Отменить выделение<br><br>"
                "<b>ПКМ + Drag</b> — Панорама<br>"
                "<b>Двойной клик</b> — Редактировать текст<br>"
                "<b>Drag</b> — Перетаскивание элементов<br><br>"
                "<b>Тема → Сменить тему</b> — Переключение темы"
            ),
        )


# ======================================================================
#  Entry point
# ======================================================================


def main():
    init_theme()
    app = QApplication(sys.argv)
    app.setStyleSheet(Styles.global_app())
    window = OCRApp()
    window.show()
    return app.exec()
