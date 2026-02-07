"""
Data models — dataclasses for Box, Line, Block.

Note: Box.get_rect() returns a PyQt6 QRectF for convenience.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from PyQt6.QtCore import QRectF


@dataclass
class Box:
    """One text box (word) stored in YOLO normalised format."""

    id: int
    image_name: str
    x_center: float
    y_center: float
    width: float
    height: float
    text: str
    line_id: Optional[int] = None
    line_order: Optional[int] = None

    def get_rect(self, img_w: int, img_h: int) -> QRectF:
        """Return absolute pixel rectangle for the given image size."""
        w = self.width * img_w
        h = self.height * img_h
        x = (self.x_center * img_w) - w / 2
        y = (self.y_center * img_h) - h / 2
        return QRectF(x, y, w, h)


@dataclass
class Line:
    """One text line — ordered list of box IDs."""

    id: int
    image_name: str
    boxes: List[int]
    text: str
    order_index: int = 0
    block_id: Optional[int] = None
    is_default: bool = False


@dataclass
class Block:
    """A logical block (group of lines)."""

    id: int
    image_name: str
    name: str
    order_index: int = 0
    lines: List[int] = field(default_factory=list)
    is_default: bool = False
