"""
Design System — adaptive dark / light theme.

Auto-detects the OS colour scheme and provides consistent styling
across the entire application.  Inspired by Roboflow and Apple HIG.
To re-skin the app, modify palettes or add a new one.
"""
import platform


# ══════════════════════════════════════════════════════════════
#  OS theme detection
# ══════════════════════════════════════════════════════════════

def _detect_dark_mode() -> bool:
    """Return *True* if the operating system is in dark mode."""
    if platform.system() == "Windows":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return val == 0
        except Exception:
            return False
    if platform.system() == "Darwin":
        try:
            import subprocess
            r = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True,
            )
            return "dark" in r.stdout.lower()
        except Exception:
            return False
    return False


# ══════════════════════════════════════════════════════════════
#  Palettes
# ══════════════════════════════════════════════════════════════

class LightPalette:
    """Apple-inspired light theme."""

    # — Backgrounds —
    BG           = "#f2f2f7"
    SURFACE      = "#ffffff"
    SURFACE_SEC  = "#f9f9fb"
    ELEVATED     = "#ffffff"
    HOVER        = "#e8e8ed"
    ACTIVE       = "#d1d1d6"

    # — Text —
    TEXT         = "#1d1d1f"
    TEXT_SEC     = "#6e6e73"
    TEXT_HINT    = "#aeaeb2"
    TEXT_ON_ACC  = "#ffffff"

    # — Borders —
    BORDER       = "#d1d1d6"
    BORDER_SEC   = "#e5e5ea"
    BORDER_SUBTLE = "#f0f0f2"

    # — Accent (blue) —
    ACCENT       = "#007aff"
    ACCENT_HOVER = "#0a84ff"
    ACCENT_BG    = "#e8f1ff"
    ACCENT_BORDER = "#9ec5ff"

    # — Semantic —
    SUCCESS      = "#34c759"
    SUCCESS_BG   = "#eafbef"
    SUCCESS_TEXT = "#1a7a33"
    WARNING      = "#ff9f0a"
    WARNING_BG   = "#fff8eb"
    WARNING_BD   = "#ffd580"
    DANGER       = "#ff3b30"
    DANGER_BG    = "#ffeceb"
    PURPLE       = "#af52de"
    PURPLE_BG    = "#f5eaff"

    # — Block —
    BLOCK_BG     = "#fffdf5"
    BLOCK_BD     = "#f0dda0"
    BLOCK_ACCENT = "#c8850f"
    BLOCK_SEL_BD = "#e8a317"

    # — Line —
    LINE_BG      = "#fafafa"
    LINE_BD      = "#e5e5ea"
    LINE_SEL_BG  = "#eafbef"
    LINE_SEL_BD  = "#34c759"
    LINE_DROP_BG = "#e8f1ff"
    LINE_DROP_BD = "#007aff"

    # — Chip —
    CHIP_BG      = "#eef3fc"
    CHIP_BD      = "#c2d4f0"
    CHIP_HOV_BG  = "#dde6f7"
    CHIP_HOV_BD  = "#9bb8e8"
    CHIP_SEL_BG  = "#007aff"
    CHIP_SEL_BD  = "#005ec4"

    # — Free panels —
    FREE_W_BG    = "#f5f5f7"
    FREE_W_BD    = "#d1d1d6"
    FREE_L_BG    = "#eef5ff"
    FREE_L_BD    = "#9ec5ff"

    # — DnD indicators —
    DND_LINE     = "#007aff"
    DND_BLOCK    = "#e8a317"

    # — Canvas (always dark) —
    CANVAS_BG    = (30, 30, 32)
    CANVAS_HEX   = "#1e1e20"

    # — Scrollbar —
    SB_BG        = "#f2f2f7"
    SB_HANDLE    = "#c7c7cc"
    SB_HAN_HOV   = "#aeaeb2"

    # — Grip —
    GRIP         = "#c7c7cc"
    GRIP_HOV     = "#8e8e93"
    GRIP_HOV_BG  = "#e5e5ea"


class DarkPalette:
    """GitHub / Roboflow-inspired dark theme."""

    # — Backgrounds —
    BG           = "#0d1117"
    SURFACE      = "#161b22"
    SURFACE_SEC  = "#1c2128"
    ELEVATED     = "#21262d"
    HOVER        = "#30363d"
    ACTIVE       = "#3a424b"

    # — Text —
    TEXT         = "#e6edf3"
    TEXT_SEC     = "#8b949e"
    TEXT_HINT    = "#6e7681"
    TEXT_ON_ACC  = "#ffffff"

    # — Borders —
    BORDER       = "#30363d"
    BORDER_SEC   = "#21262d"
    BORDER_SUBTLE = "#1b2028"

    # — Accent (blue) —
    ACCENT       = "#58a6ff"
    ACCENT_HOVER = "#79c0ff"
    ACCENT_BG    = "#152238"
    ACCENT_BORDER = "#1f6feb"

    # — Semantic —
    SUCCESS      = "#3fb950"
    SUCCESS_BG   = "#122d1b"
    SUCCESS_TEXT = "#7ee787"
    WARNING      = "#d29922"
    WARNING_BG   = "#2a2009"
    WARNING_BD   = "#9e6a03"
    DANGER       = "#f85149"
    DANGER_BG    = "#3d1418"
    PURPLE       = "#bc8cff"
    PURPLE_BG    = "#231845"

    # — Block —
    BLOCK_BG     = "#1f1b12"
    BLOCK_BD     = "#4a3d1a"
    BLOCK_ACCENT = "#d29922"
    BLOCK_SEL_BD = "#e3b341"

    # — Line —
    LINE_BG      = "#1c2128"
    LINE_BD      = "#21262d"
    LINE_SEL_BG  = "#122d1b"
    LINE_SEL_BD  = "#3fb950"
    LINE_DROP_BG = "#152238"
    LINE_DROP_BD = "#58a6ff"

    # — Chip —
    CHIP_BG      = "#152238"
    CHIP_BD      = "#1f4a7a"
    CHIP_HOV_BG  = "#1a3a5c"
    CHIP_HOV_BD  = "#2d6cb5"
    CHIP_SEL_BG  = "#58a6ff"
    CHIP_SEL_BD  = "#79c0ff"

    # — Free panels —
    FREE_W_BG    = "#21262d"
    FREE_W_BD    = "#30363d"
    FREE_L_BG    = "#141d2b"
    FREE_L_BD    = "#1f4a7a"

    # — DnD indicators —
    DND_LINE     = "#58a6ff"
    DND_BLOCK    = "#d29922"

    # — Canvas —
    CANVAS_BG    = (13, 17, 23)
    CANVAS_HEX   = "#0d1117"

    # — Scrollbar —
    SB_BG        = "#0d1117"
    SB_HANDLE    = "#30363d"
    SB_HAN_HOV   = "#484f58"

    # — Grip —
    GRIP         = "#484f58"
    GRIP_HOV     = "#8b949e"
    GRIP_HOV_BG  = "#30363d"


# ══════════════════════════════════════════════════════════════
#  Theme state  (module-level singleton)
# ══════════════════════════════════════════════════════════════

_is_dark: bool = False
_p = LightPalette  # active palette reference


def init_theme(force_dark: bool = None):
    """Call once at startup.  *force_dark* overrides auto-detection."""
    global _is_dark, _p
    _is_dark = force_dark if force_dark is not None else _detect_dark_mode()
    _p = DarkPalette if _is_dark else LightPalette


def set_dark(dark: bool):
    """Switch palette at runtime."""
    global _is_dark, _p
    _is_dark = dark
    _p = DarkPalette if dark else LightPalette


def is_dark() -> bool:
    return _is_dark


def palette():
    """Return the active palette class."""
    return _p


# ══════════════════════════════════════════════════════════════
#  Typography & tokens
# ══════════════════════════════════════════════════════════════

class Font:
    FAMILY = ("'Segoe UI Variable', 'Segoe UI', 'SF Pro Display', "
              "'Helvetica Neue', system-ui, sans-serif")
    XS   = "10px"
    SM   = "11px"
    BASE = "13px"
    MD   = "14px"
    LG   = "16px"
    XL   = "18px"


class Radius:
    XS   = "4px"
    SM   = "6px"
    MD   = "10px"
    LG   = "14px"
    XL   = "20px"
    PILL = "100px"


def shadow_color():
    """QColor for QGraphicsDropShadowEffect."""
    from PyQt6.QtGui import QColor
    return QColor(0, 0, 0, 15 if not _is_dark else 70)


# ══════════════════════════════════════════════════════════════
#  Stylesheet factory
# ══════════════════════════════════════════════════════════════

class Styles:
    """Ready-to-use stylesheet strings — call e.g. ``Styles.button()``."""

    # ── Global (applied to QApplication) ──

    @staticmethod
    def global_app() -> str:
        return f"""
            * {{ font-family: {Font.FAMILY}; }}
            QToolTip {{
                background: {_p.ELEVATED}; color: {_p.TEXT};
                border: 1px solid {_p.BORDER}; border-radius: {Radius.SM};
                padding: 6px 10px; font-size: {Font.SM};
            }}
            QMessageBox {{
                background: {_p.SURFACE};
            }}
            QMessageBox QLabel {{
                color: {_p.TEXT}; font-size: {Font.BASE};
            }}
            QMessageBox QPushButton {{
                background: {_p.ACCENT}; color: {_p.TEXT_ON_ACC};
                border: none; border-radius: {Radius.MD};
                padding: 8px 20px; font-weight: 600; min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background: {_p.ACCENT_HOVER};
            }}
            QInputDialog {{
                background: {_p.SURFACE};
            }}
            QInputDialog QLabel {{
                color: {_p.TEXT}; font-size: {Font.BASE};
            }}
            QInputDialog QLineEdit, QInputDialog QSpinBox {{
                background: {_p.BG}; color: {_p.TEXT};
                border: 1px solid {_p.BORDER}; border-radius: {Radius.SM};
                padding: 6px 10px; font-size: {Font.BASE};
            }}
            QInputDialog QLineEdit:focus, QInputDialog QSpinBox:focus {{
                border-color: {_p.ACCENT};
            }}
            QInputDialog QPushButton {{
                background: {_p.ACCENT}; color: {_p.TEXT_ON_ACC};
                border: none; border-radius: {Radius.SM};
                padding: 8px 20px; font-weight: 600;
            }}
            QInputDialog QPushButton:hover {{
                background: {_p.ACCENT_HOVER};
            }}
        """

    # ── Main Window & Menus ──

    @staticmethod
    def main_window() -> str:
        return f"""
            QMainWindow {{ background: {_p.BG}; border-radius: {Radius.LG}; }}
            QMenuBar {{
                background: {_p.SURFACE}; color: {_p.TEXT};
                border-bottom: 1px solid {_p.BORDER};
                font-family: {Font.FAMILY}; font-size: {Font.BASE};
                padding: 2px 0;
            }}
            QMenuBar::item {{
                background: transparent; color: {_p.TEXT};
                padding: 6px 12px; border-radius: {Radius.SM};
            }}
            QMenuBar::item:selected {{
                background: {_p.ACCENT_BG}; color: {_p.ACCENT};
            }}
            QMenu {{
                background: {_p.SURFACE}; border: 1px solid {_p.BORDER};
                border-radius: {Radius.MD}; padding: 4px;
                font-family: {Font.FAMILY}; font-size: {Font.BASE};
            }}
            QMenu::item {{
                color: {_p.TEXT}; padding: 8px 24px 8px 16px;
                border-radius: {Radius.SM};
            }}
            QMenu::item:selected {{
                background: {_p.ACCENT_BG}; color: {_p.ACCENT};
            }}
            QMenu::item:disabled {{ color: {_p.TEXT_HINT}; }}
            QMenu::separator {{
                height: 1px; background: {_p.BORDER_SEC}; margin: 4px 8px;
            }}
        """

    # ── Grip ──

    @staticmethod
    def drag_grip() -> str:
        return f"""
            QLabel {{
                color: {_p.GRIP}; font-size: {Font.SM}; padding: 0;
                background: transparent;
            }}
            QLabel:hover {{
                color: {_p.GRIP_HOV};
                background: {_p.GRIP_HOV_BG}; border-radius: 3px;
            }}
        """

    # ── WordChip ──

    @staticmethod
    def word_chip_normal() -> str:
        return f"""
            WordChip {{
                background: {_p.CHIP_BG};
                border: 1px solid {_p.CHIP_BD};
                border-radius: {Radius.PILL};
            }}
            WordChip:hover {{
                background: {_p.CHIP_HOV_BG};
                border-color: {_p.CHIP_HOV_BD};
            }}
            WordChip QLabel {{
                color: {_p.TEXT}; background: transparent;
                border: none; padding: 2px 5px;
                font-size: {Font.SM};
            }}
        """

    @staticmethod
    def word_chip_selected() -> str:
        return f"""
            WordChip {{
                background: {_p.CHIP_SEL_BG};
                border: 2px solid {_p.CHIP_SEL_BD};
                border-radius: {Radius.PILL};
            }}
            WordChip QLabel {{
                color: {_p.TEXT_ON_ACC}; background: transparent;
                border: none; padding: 2px 5px;
                font-size: {Font.SM};
            }}
        """

    # ── LineWidget ──

    @staticmethod
    def line_normal() -> str:
        return f"""
            LineWidget {{
                background: {_p.LINE_BG};
                border: 1px solid {_p.LINE_BD}; border-radius: {Radius.MD};
                margin: 3px 0;
            }}
            LineWidget:hover {{
                background: {_p.HOVER};
                border-color: {_p.ACCENT_BORDER};
            }}
        """

    @staticmethod
    def line_selected() -> str:
        return f"""
            LineWidget {{
                background: {_p.LINE_SEL_BG};
                border: 2px solid {_p.LINE_SEL_BD}; border-radius: {Radius.MD};
                margin: 3px 0;
            }}
        """

    @staticmethod
    def line_drop_target() -> str:
        return f"""
            LineWidget {{
                background: {_p.LINE_DROP_BG};
                border: 2px dashed {_p.LINE_DROP_BD}; border-radius: {Radius.MD};
                margin: 3px 0;
            }}
        """

    # ── BlockWidget ──

    @staticmethod
    def block_normal() -> str:
        return f"""
            BlockWidget {{
                background: {_p.BLOCK_BG};
                border: 1px solid {_p.BLOCK_BD}; border-radius: {Radius.LG};
                margin: 8px 0;
            }}
            BlockWidget:hover {{ border-color: {_p.BLOCK_ACCENT}; }}
        """

    @staticmethod
    def block_selected() -> str:
        return f"""
            BlockWidget {{
                background: {_p.BLOCK_BG};
                border: 2px solid {_p.BLOCK_SEL_BD}; border-radius: {Radius.LG};
                margin: 8px 0;
            }}
        """

    @staticmethod
    def block_drop_target() -> str:
        return f"""
            BlockWidget {{
                background: {_p.WARNING_BG};
                border: 2px dashed {_p.WARNING}; border-radius: {Radius.LG};
                margin: 8px 0;
            }}
        """

    @staticmethod
    def block_header() -> str:
        return f"""
            font-weight: 700; color: {_p.BLOCK_ACCENT};
            font-size: {Font.MD}; font-family: {Font.FAMILY};
            padding: 4px 6px; background: transparent;
        """

    # ── Free-element panels ──

    @staticmethod
    def free_lines_panel() -> str:
        return f"""
            FreeLinesPanel {{
                background: {_p.FREE_L_BG};
                border: 1px dashed {_p.FREE_L_BD};
                border-radius: {Radius.LG}; margin: 6px 0; min-height: 48px;
            }}
        """

    @staticmethod
    def free_lines_panel_drop() -> str:
        return f"""
            FreeLinesPanel {{
                background: {_p.ACCENT_BG};
                border: 2px dashed {_p.ACCENT};
                border-radius: {Radius.LG}; margin: 6px 0; min-height: 48px;
            }}
        """

    @staticmethod
    def free_words_panel() -> str:
        return f"""
            FreeWordsPanel {{
                background: {_p.FREE_W_BG};
                border: 1px dashed {_p.FREE_W_BD};
                border-radius: {Radius.LG}; margin: 6px 0; min-height: 48px;
            }}
        """

    @staticmethod
    def free_words_panel_drop() -> str:
        return f"""
            FreeWordsPanel {{
                background: {_p.SUCCESS_BG};
                border: 2px dashed {_p.SUCCESS};
                border-radius: {Radius.LG}; margin: 6px 0; min-height: 48px;
            }}
        """

    # ── StructurePanel (scroll area) ──

    @staticmethod
    def structure_scroll() -> str:
        return f"""
            QScrollArea {{
                background: {_p.BG};
                border: 1px solid {_p.BORDER_SEC};
                border-radius: {Radius.SM};
                margin: 2px 4px 4px 0;
            }}
            QScrollArea > QWidget > QWidget {{
                background: {_p.BG};
            }}
            QScrollBar:vertical {{
                background: transparent; width: 6px;
                margin: 4px 1px; border: none;
            }}
            QScrollBar:horizontal {{
                background: transparent; height: 6px;
                margin: 1px 4px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {_p.SB_HANDLE}; border-radius: 3px;
                min-height: 40px;
            }}
            QScrollBar::handle:horizontal {{
                background: {_p.SB_HANDLE}; border-radius: 3px;
                min-width: 40px;
            }}
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
                background: {_p.SB_HAN_HOV};
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; background: none; }}
            QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
        """

    @staticmethod
    def section_header() -> str:
        return f"""
            font-weight: 700; color: {_p.TEXT_SEC};
            font-size: {Font.SM}; font-family: {Font.FAMILY};
            padding: 16px 4px 6px 4px;
            border-bottom: 1.5px solid {_p.BORDER_SEC};
            margin-bottom: 6px;
        """

    @staticmethod
    def panel_header() -> str:
        return f"""
            padding: 0 20px; background: {_p.SURFACE};
            color: {_p.TEXT}; font-size: {Font.LG};
            font-weight: 700; font-family: {Font.FAMILY};
            border: 1px solid {_p.BORDER_SEC};
            border-radius: {Radius.SM};
            margin: 2px 4px 0 0;
            min-height: 44px; max-height: 44px;
        """

    # ── Buttons ──

    @staticmethod
    def button() -> str:
        return f"""
            QPushButton {{
                background: {_p.SURFACE}; border: 1px solid {_p.BORDER};
                border-radius: {Radius.MD}; color: {_p.TEXT};
                padding: 8px 18px; font-size: {Font.SM};
                font-family: {Font.FAMILY}; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {_p.HOVER}; border-color: {_p.ACCENT_BORDER};
            }}
            QPushButton:pressed {{ background: {_p.ACTIVE}; }}
        """

    @staticmethod
    def button_primary() -> str:
        return f"""
            QPushButton {{
                background: {_p.ACCENT}; border: 1px solid {_p.ACCENT};
                border-radius: {Radius.MD}; color: {_p.TEXT_ON_ACC};
                padding: 6px 14px; font-size: {Font.SM};
                font-family: {Font.FAMILY}; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {_p.ACCENT_HOVER}; border-color: {_p.ACCENT_HOVER};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        return f"""
            QPushButton {{
                background: {_p.DANGER_BG}; border: 1px solid {_p.DANGER};
                border-radius: {Radius.MD}; color: {_p.DANGER};
                padding: 8px 18px; font-size: {Font.SM};
                font-family: {Font.FAMILY}; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {_p.DANGER}; color: {_p.TEXT_ON_ACC};
                border-color: {_p.DANGER};
            }}
        """

    @staticmethod
    def nav_button() -> str:
        return f"""
            QPushButton {{
                background: {_p.SURFACE}; border: 1px solid {_p.BORDER};
                border-radius: {Radius.SM}; color: {_p.TEXT};
                font-size: {Font.BASE}; font-weight: 600; padding: 2px 6px;
            }}
            QPushButton:hover {{
                background: {_p.HOVER}; border-color: {_p.BORDER};
            }}
            QPushButton:pressed {{ background: {_p.ACTIVE}; }}
            QPushButton:disabled {{
                color: {_p.TEXT_HINT}; background: {_p.SURFACE_SEC};
                border-color: {_p.BORDER_SEC};
            }}
        """

    @staticmethod
    def toggle_button() -> str:
        return f"""
            QPushButton {{
                background: {_p.SURFACE}; border: 1.5px solid {_p.BORDER};
                border-radius: {Radius.SM}; color: {_p.TEXT_SEC};
                padding: 4px 12px; font-size: {Font.SM};
                font-family: {Font.FAMILY}; font-weight: 600;
            }}
            QPushButton:hover {{
                background: {_p.HOVER}; border-color: {_p.ACCENT_BORDER};
                color: {_p.TEXT};
            }}
            QPushButton:checked {{
                background: {_p.ACCENT_BG}; border-color: {_p.ACCENT};
                color: {_p.ACCENT};
            }}
            QPushButton:checked:hover {{
                background: {_p.ACCENT}; color: {_p.TEXT_ON_ACC};
            }}
        """

    @staticmethod
    def zoom_button() -> str:
        return f"""
            QPushButton {{
                background: transparent; border: none;
                border-radius: {Radius.SM};
                color: {_p.TEXT_SEC}; font-size: {Font.LG};
                font-weight: 600; padding: 4px;
            }}
            QPushButton:hover {{
                background: {_p.HOVER}; color: {_p.TEXT};
            }}
            QPushButton:pressed {{ background: {_p.ACTIVE}; }}
        """

    # ── Labels ──

    @staticmethod
    def filename_label() -> str:
        return f"""
            padding: 4px 10px; background: {_p.SURFACE};
            color: {_p.ACCENT}; font-size: {Font.BASE};
            font-family: {Font.FAMILY}; font-weight: 500;
            border-radius: {Radius.SM}; border: 1px solid {_p.BORDER_SEC};
        """

    @staticmethod
    def filename_label_copied() -> str:
        return f"""
            padding: 4px 10px; background: {_p.SUCCESS_BG};
            color: {_p.SUCCESS}; font-size: {Font.BASE};
            font-family: {Font.FAMILY}; font-weight: 500;
            border-radius: {Radius.SM}; border: 1px solid {_p.SUCCESS};
        """

    @staticmethod
    def page_label() -> str:
        return f"""
            padding: 5px 14px; background: {_p.ACCENT_BG};
            color: {_p.ACCENT}; font-size: {Font.BASE};
            font-weight: 700; font-family: {Font.FAMILY};
            border-radius: {Radius.SM}; border: 1px solid {_p.ACCENT_BORDER};
        """

    @staticmethod
    def status_label() -> str:
        return f"""
            padding: 4px 10px; background: transparent;
            color: {_p.TEXT_SEC}; font-size: {Font.SM};
            font-family: {Font.FAMILY};
        """

    @staticmethod
    def zoom_label() -> str:
        return f"""
            background: transparent; color: {_p.TEXT_SEC};
            font-size: {Font.SM}; font-family: {Font.FAMILY};
            padding: 4px;
        """

    @staticmethod
    def status_bar_container() -> str:
        return f"""
            background: {_p.SURFACE};
            border: 1px solid {_p.BORDER_SEC};
            border-radius: {Radius.SM};
            margin: 4px 4px 2px 4px;
        """

    # ── Viewer ──

    @staticmethod
    def viewer_scroll() -> str:
        return f"""
            QScrollArea {{
                border: 1px solid {_p.BORDER_SEC};
                background: {_p.CANVAS_HEX};
                border-radius: {Radius.SM};
                margin: 2px 0 4px 4px;
            }}
        """

    # ── Splitter ──

    @staticmethod
    def splitter() -> str:
        return f"""
            QSplitter {{
                background: {_p.BG};
            }}
            QSplitter::handle {{
                background: {_p.BORDER_SEC}; width: 4px;
                margin: 12px 0; border-radius: 2px;
            }}
            QSplitter::handle:hover {{
                background: {_p.ACCENT_BORDER};
            }}
        """

    # ── Dialog ──

    @staticmethod
    def dialog() -> str:
        return f"""
            QDialog {{
                background: {_p.SURFACE};
                font-family: {Font.FAMILY};
            }}
            QLabel {{
                color: {_p.TEXT}; font-size: {Font.BASE};
            }}
            QLineEdit {{
                background: {_p.BG}; color: {_p.TEXT};
                border: 1.5px solid {_p.BORDER}; border-radius: {Radius.MD};
                padding: 10px 14px; font-size: {Font.BASE};
                font-family: {Font.FAMILY};
                selection-background-color: {_p.ACCENT};
                selection-color: {_p.TEXT_ON_ACC};
            }}
            QLineEdit:focus {{
                border-color: {_p.ACCENT}; background: {_p.SURFACE};
            }}
            QDialogButtonBox QPushButton {{
                background: {_p.ACCENT}; color: {_p.TEXT_ON_ACC};
                border: none; border-radius: {Radius.MD};
                padding: 10px 28px; font-weight: 600;
                min-width: 90px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background: {_p.ACCENT_HOVER};
            }}
        """

    @staticmethod
    def spin_box() -> str:
        return f"""
            QSpinBox {{
                background: {_p.BG}; color: {_p.TEXT};
                border: 1.5px solid {_p.BORDER}; border-radius: {Radius.MD};
                padding: 6px 10px; font-size: {Font.BASE};
                font-family: {Font.FAMILY}; font-weight: 600;
                selection-background-color: {_p.ACCENT};
                selection-color: {_p.TEXT_ON_ACC};
            }}
            QSpinBox:focus {{
                border-color: {_p.ACCENT}; background: {_p.SURFACE};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0; height: 0; border: none;
            }}
        """
