"""
SQLite database layer — unified hierarchy.

Every word → line → block.  No NULL foreign keys.
Each image has a *default* block and a *default* line that serve as
a catch-all for newly-created or "freed" annotations.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional

from .data import Box, Line, Block


class OCRDatabase:
    """All annotation persistence lives here."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    # ------------------------------------------------------------------
    #  Connection helper
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self):
        """Yield a *sqlite3.Connection* that auto-commits on clean exit."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    #  Schema / migrations
    # ------------------------------------------------------------------

    def _init_schema(self):
        with self._connect() as conn:
            c = conn.cursor()

            c.execute("""CREATE TABLE IF NOT EXISTS annotations
                         (id INTEGER PRIMARY KEY,
                          image_name TEXT,
                          x_center REAL, y_center REAL,
                          width REAL, height REAL,
                          decoding TEXT,
                          line_id INTEGER,
                          line_order INTEGER)""")

            c.execute("""CREATE TABLE IF NOT EXISTS lines
                         (id INTEGER PRIMARY KEY,
                          image_name TEXT,
                          text TEXT,
                          created_at TEXT,
                          order_index INTEGER DEFAULT 0,
                          block_id INTEGER,
                          is_default INTEGER DEFAULT 0)""")

            c.execute("""CREATE TABLE IF NOT EXISTS blocks
                         (id INTEGER PRIMARY KEY,
                          image_name TEXT,
                          name TEXT,
                          order_index INTEGER DEFAULT 0,
                          is_default INTEGER DEFAULT 0)""")

            # Migrations for older DBs
            for table, col, col_def in [
                ("annotations", "line_id", "INTEGER"),
                ("annotations", "line_order", "INTEGER"),
                ("lines", "order_index", "INTEGER DEFAULT 0"),
                ("lines", "block_id", "INTEGER"),
                ("lines", "is_default", "INTEGER DEFAULT 0"),
                ("blocks", "is_default", "INTEGER DEFAULT 0"),
            ]:
                c.execute(f"PRAGMA table_info({table})")
                existing = {row[1] for row in c.fetchall()}
                if col not in existing:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")

    # ------------------------------------------------------------------
    #  Default block & line  (unified hierarchy guarantee)
    # ------------------------------------------------------------------

    def ensure_defaults(self, image_name: str) -> tuple:
        """Guarantee a default block + default line exist for *image_name*.

        Returns ``(default_block_id, default_line_id)``.
        Also migrates any orphaned rows (``line_id IS NULL``, etc.).
        """
        with self._connect() as conn:
            c = conn.cursor()

            # --- Default block ---
            c.execute(
                "SELECT id FROM blocks WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            if row:
                block_id = row[0]
            else:
                c.execute(
                    "INSERT INTO blocks (image_name, name, order_index, is_default) "
                    "VALUES (?, ?, 999999, 1)",
                    (image_name, "Нераспределённые"),
                )
                block_id = c.lastrowid

            # --- Default line ---
            c.execute(
                "SELECT id FROM lines WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            if row:
                line_id = row[0]
            else:
                c.execute(
                    "INSERT INTO lines "
                    "(image_name, text, created_at, order_index, block_id, is_default) "
                    "VALUES (?, '', datetime('now'), 999999, ?, 1)",
                    (image_name, block_id),
                )
                line_id = c.lastrowid

            # --- Fixup orphaned boxes (line_id IS NULL → default line) ---
            c.execute(
                "SELECT id FROM annotations WHERE image_name = ? AND line_id IS NULL",
                (image_name,),
            )
            orphaned_boxes = [r[0] for r in c.fetchall()]
            if orphaned_boxes:
                c.execute(
                    "SELECT COALESCE(MAX(line_order), -1) FROM annotations "
                    "WHERE line_id = ?",
                    (line_id,),
                )
                start = c.fetchone()[0] + 1
                for i, bid in enumerate(orphaned_boxes):
                    c.execute(
                        "UPDATE annotations SET line_id=?, line_order=? WHERE id=?",
                        (line_id, start + i, bid),
                    )

            # --- Fixup orphaned lines (block_id IS NULL → default block) ---
            c.execute(
                "UPDATE lines SET block_id = ? "
                "WHERE image_name = ? AND block_id IS NULL AND is_default = 0",
                (block_id, image_name),
            )

            return block_id, line_id

    def get_default_line_id(self, image_name: str) -> Optional[int]:
        """Return the default line id (or None if ensure_defaults not yet called)."""
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id FROM lines WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            return row[0] if row else None

    def get_default_block_id(self, image_name: str) -> Optional[int]:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id FROM blocks WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            return row[0] if row else None

    # ------------------------------------------------------------------
    #  Reads
    # ------------------------------------------------------------------

    def get_boxes(self, image_name: str) -> List[Box]:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, image_name, x_center, y_center, width, height, "
                "decoding, line_id, line_order FROM annotations WHERE image_name = ?",
                (image_name,),
            )
            return [
                Box(id=r[0], image_name=r[1], x_center=r[2], y_center=r[3],
                    width=r[4], height=r[5], text=r[6] or "",
                    line_id=r[7], line_order=r[8])
                for r in c.fetchall()
            ]

    def get_lines(self, image_name: str) -> List[Line]:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, text, order_index, block_id, is_default FROM lines "
                "WHERE image_name = ? ORDER BY is_default, block_id, order_index, id",
                (image_name,),
            )
            lines: List[Line] = []
            for row in c.fetchall():
                lid = row[0]
                c.execute(
                    "SELECT id FROM annotations WHERE line_id = ? ORDER BY line_order",
                    (lid,),
                )
                box_ids = [r[0] for r in c.fetchall()]
                lines.append(
                    Line(id=lid, image_name=image_name, boxes=box_ids,
                         text=row[1] or "", order_index=row[2] or 0,
                         block_id=row[3], is_default=bool(row[4]))
                )
            return lines

    def get_blocks(self, image_name: str) -> List[Block]:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, name, order_index, is_default FROM blocks "
                "WHERE image_name = ? ORDER BY is_default, order_index, id",
                (image_name,),
            )
            blocks: List[Block] = []
            for row in c.fetchall():
                bid = row[0]
                c.execute(
                    "SELECT id FROM lines WHERE block_id = ? ORDER BY is_default, order_index",
                    (bid,),
                )
                line_ids = [r[0] for r in c.fetchall()]
                blocks.append(
                    Block(id=bid, image_name=image_name,
                          name=row[1] or "", order_index=row[2] or 0,
                          lines=line_ids, is_default=bool(row[3]))
                )
            return blocks

    # ------------------------------------------------------------------
    #  Block CRUD
    # ------------------------------------------------------------------

    def create_block(self, image_name: str, name: str = "") -> int:
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT MAX(order_index) FROM blocks "
                "WHERE image_name = ? AND is_default = 0",
                (image_name,),
            )
            next_order = (c.fetchone()[0] or 0) + 1
            c.execute(
                "INSERT INTO blocks (image_name, name, order_index, is_default) "
                "VALUES (?, ?, ?, 0)",
                (image_name, name or f"Блок {next_order}", next_order),
            )
            return c.lastrowid

    def update_block_name(self, block_id: int, name: str):
        with self._connect() as conn:
            conn.cursor().execute(
                "UPDATE blocks SET name = ? WHERE id = ?", (name, block_id)
            )

    def delete_block(self, block_id: int):
        """Delete a block — its lines move to the default block."""
        with self._connect() as conn:
            c = conn.cursor()
            # Prevent deleting the default block
            c.execute("SELECT is_default, image_name FROM blocks WHERE id = ?", (block_id,))
            row = c.fetchone()
            if not row or row[0] == 1:
                return
            image_name = row[1]

            # Find default block for this image
            c.execute(
                "SELECT id FROM blocks WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            default = c.fetchone()
            default_block_id = default[0] if default else None

            # Move lines to default block
            c.execute(
                "UPDATE lines SET block_id = ? WHERE block_id = ?",
                (default_block_id, block_id),
            )
            c.execute("DELETE FROM blocks WHERE id = ?", (block_id,))

    # ------------------------------------------------------------------
    #  Line CRUD
    # ------------------------------------------------------------------

    def create_line(self, image_name: str, box_ids: List[int]) -> int:
        """Create a regular line in the default block.

        Boxes are moved from wherever they are to this new line.
        """
        with self._connect() as conn:
            c = conn.cursor()

            # Default block
            c.execute(
                "SELECT id FROM blocks WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            default_block_id = row[0] if row else None

            c.execute(
                "SELECT MAX(order_index) FROM lines "
                "WHERE image_name = ? AND is_default = 0",
                (image_name,),
            )
            next_order = (c.fetchone()[0] or 0) + 1

            line_text = ""
            if box_ids:
                ph = ",".join("?" * len(box_ids))
                c.execute(
                    f"SELECT id, decoding FROM annotations WHERE id IN ({ph})",
                    box_ids,
                )
                id_text = {r[0]: (r[1] or "") for r in c.fetchall()}
                line_text = " ".join(id_text.get(bid, "") for bid in box_ids)

            c.execute(
                "INSERT INTO lines "
                "(image_name, text, created_at, order_index, block_id, is_default) "
                "VALUES (?, ?, ?, ?, ?, 0)",
                (image_name, line_text, datetime.now().isoformat(),
                 next_order, default_block_id),
            )
            line_id = c.lastrowid
            for idx, bid in enumerate(box_ids):
                c.execute(
                    "UPDATE annotations SET line_id=?, line_order=? WHERE id=?",
                    (line_id, idx, bid),
                )
            return line_id

    def update_line_text(self, line_id: int, text: str):
        with self._connect() as conn:
            conn.cursor().execute(
                "UPDATE lines SET text = ? WHERE id = ?", (text, line_id)
            )

    def delete_line(self, line_id: int):
        """Delete a line — its boxes move to the default line."""
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT is_default, image_name FROM lines WHERE id = ?",
                (line_id,),
            )
            row = c.fetchone()
            if not row or row[0] == 1:
                return  # can't delete the default line
            image_name = row[1]

            # Find default line
            c.execute(
                "SELECT id FROM lines WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            default = c.fetchone()
            default_line_id = default[0] if default else None

            # Move boxes to default line
            if default_line_id:
                c.execute(
                    "SELECT COALESCE(MAX(line_order), -1) FROM annotations "
                    "WHERE line_id = ?",
                    (default_line_id,),
                )
                start = c.fetchone()[0] + 1
                c.execute(
                    "SELECT id FROM annotations WHERE line_id = ? ORDER BY line_order",
                    (line_id,),
                )
                for i, (bid,) in enumerate(c.fetchall()):
                    c.execute(
                        "UPDATE annotations SET line_id=?, line_order=? WHERE id=?",
                        (default_line_id, start + i, bid),
                    )
            else:
                c.execute(
                    "UPDATE annotations SET line_id=NULL, line_order=NULL "
                    "WHERE line_id=?",
                    (line_id,),
                )

            c.execute("DELETE FROM lines WHERE id = ?", (line_id,))

    def update_lines_order(self, image_name: str, line_ids_in_order: List[int]):
        with self._connect() as conn:
            c = conn.cursor()
            for idx, lid in enumerate(line_ids_in_order):
                c.execute(
                    "UPDATE lines SET order_index = ? WHERE id = ?",
                    (idx + 1, lid),
                )

    def move_line_to_block(self, line_id: int, block_id: Optional[int]):
        """Move a line to *block_id*.  ``None`` → default block."""
        with self._connect() as conn:
            c = conn.cursor()
            if block_id is None:
                c.execute("SELECT image_name FROM lines WHERE id = ?", (line_id,))
                row = c.fetchone()
                if row:
                    c.execute(
                        "SELECT id FROM blocks "
                        "WHERE image_name = ? AND is_default = 1",
                        (row[0],),
                    )
                    d = c.fetchone()
                    block_id = d[0] if d else None
            c.execute(
                "UPDATE lines SET block_id = ? WHERE id = ?",
                (block_id, line_id),
            )

    def reorder_line_in_block(self, line_id: int, block_id: int,
                              new_position: int):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id FROM lines WHERE block_id = ? AND is_default = 0 "
                "ORDER BY order_index",
                (block_id,),
            )
            lines = [r[0] for r in c.fetchall()]
            if line_id in lines:
                lines.remove(line_id)
            new_position = max(0, min(new_position, len(lines)))
            lines.insert(new_position, line_id)
            for idx, lid in enumerate(lines):
                c.execute(
                    "UPDATE lines SET order_index = ? WHERE id = ?",
                    (idx, lid),
                )

    # ------------------------------------------------------------------
    #  Box CRUD
    # ------------------------------------------------------------------

    def create_box(self, image_name: str, x_center: float, y_center: float,
                   width: float, height: float, text: str = "") -> int:
        """Create a box — auto-assigns to the default line."""
        with self._connect() as conn:
            c = conn.cursor()
            # Get default line
            c.execute(
                "SELECT id FROM lines WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            default_line_id = row[0] if row else None

            next_order = 0
            if default_line_id:
                c.execute(
                    "SELECT COALESCE(MAX(line_order), -1) + 1 "
                    "FROM annotations WHERE line_id = ?",
                    (default_line_id,),
                )
                next_order = c.fetchone()[0]

            c.execute(
                "INSERT INTO annotations "
                "(image_name, x_center, y_center, width, height, decoding, "
                "line_id, line_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (image_name, x_center, y_center, width, height, text,
                 default_line_id, next_order),
            )
            return c.lastrowid

    def update_box(self, box_id: int, x_center: float, y_center: float,
                   width: float, height: float):
        with self._connect() as conn:
            conn.cursor().execute(
                "UPDATE annotations SET x_center=?, y_center=?, "
                "width=?, height=? WHERE id=?",
                (x_center, y_center, width, height, box_id),
            )

    def update_box_text(self, box_id: int, text: str):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE annotations SET decoding=? WHERE id=?",
                (text, box_id),
            )
            c.execute("SELECT line_id FROM annotations WHERE id=?", (box_id,))
            row = c.fetchone()
            if row and row[0]:
                self._refresh_line_text(c, row[0])

    def delete_box(self, box_id: int):
        with self._connect() as conn:
            c = conn.cursor()
            c.execute("SELECT line_id FROM annotations WHERE id=?", (box_id,))
            row = c.fetchone()
            line_id = row[0] if row else None

            c.execute("DELETE FROM annotations WHERE id=?", (box_id,))

            if line_id:
                c.execute(
                    "SELECT decoding FROM annotations "
                    "WHERE line_id=? ORDER BY line_order",
                    (line_id,),
                )
                texts = [r[0] or "" for r in c.fetchall()]
                if texts:
                    c.execute(
                        "UPDATE lines SET text=? WHERE id=?",
                        (" ".join(texts), line_id),
                    )
                else:
                    # Empty non-default line → delete it
                    c.execute(
                        "SELECT is_default FROM lines WHERE id = ?",
                        (line_id,),
                    )
                    r = c.fetchone()
                    if r and r[0] != 1:
                        c.execute("DELETE FROM lines WHERE id=?", (line_id,))

    def move_box_to_line(self, box_id: int, line_id: Optional[int],
                         order: Optional[int] = None):
        """Move a box to *line_id*.  ``None`` → default line."""
        with self._connect() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT line_id, image_name FROM annotations WHERE id = ?",
                (box_id,),
            )
            row = c.fetchone()
            old_line_id = row[0] if row else None
            img_name = row[1] if row else None

            # None → default line
            if line_id is None and img_name:
                c.execute(
                    "SELECT id FROM lines WHERE image_name = ? AND is_default = 1",
                    (img_name,),
                )
                d = c.fetchone()
                line_id = d[0] if d else None

            if order is None and line_id is not None:
                c.execute(
                    "SELECT MAX(line_order) FROM annotations WHERE line_id = ?",
                    (line_id,),
                )
                order = (c.fetchone()[0] or 0) + 1
            elif order is None:
                order = 0

            c.execute(
                "UPDATE annotations SET line_id=?, line_order=? WHERE id=?",
                (line_id, order, box_id),
            )
            if old_line_id:
                self._refresh_line_text(c, old_line_id)
            if line_id:
                self._refresh_line_text(c, line_id)

    def update_box_order_in_line(self, line_id: int,
                                 box_ids_in_order: List[int]):
        with self._connect() as conn:
            c = conn.cursor()
            for idx, bid in enumerate(box_ids_in_order):
                c.execute(
                    "UPDATE annotations SET line_order = ? WHERE id = ?",
                    (idx, bid),
                )
            self._refresh_line_text(c, line_id)

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _refresh_line_text(cursor, line_id: int):
        """Rebuild line text from its boxes."""
        cursor.execute(
            "SELECT decoding FROM annotations "
            "WHERE line_id = ? ORDER BY line_order",
            (line_id,),
        )
        line_text = " ".join(r[0] or "" for r in cursor.fetchall())
        cursor.execute(
            "UPDATE lines SET text = ? WHERE id = ?",
            (line_text, line_id),
        )
