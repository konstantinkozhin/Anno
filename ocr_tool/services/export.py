"""
Export / Import service — JSON serialisation (COCO-like format).

Handles the mapping between the unified DB hierarchy (every word → line
→ block) and the export format with free_words / free_lines / blocks.
Also supports COCO-format import/export (images + annotations + categories).
"""
import os
import sqlite3
from typing import Optional, List

from PyQt6.QtGui import QImage

from ..models.data import Box, Line, Block
from ..models.database import OCRDatabase


class ExportService:
    """Stateless helper: build JSON-ready dicts and import them back."""

    # ------------------------------------------------------------------
    #  Export one page  →  dict
    # ------------------------------------------------------------------

    @staticmethod
    def build_page(db: OCRDatabase, image_folder: str,
                   image_name: str) -> dict:
        """Return a JSON-serialisable dict for *image_name*.

        Default block  →  free_lines + free_words.
        Regular blocks →  blocks list.
        """
        boxes = db.get_boxes(image_name)
        lines = db.get_lines(image_name)
        blocks = db.get_blocks(image_name)

        img = QImage(os.path.join(image_folder, image_name))
        img_w, img_h = img.width(), img.height()

        box_map = {b.id: b for b in boxes}
        line_map = {ln.id: ln for ln in lines}

        default_block = next((b for b in blocks if b.is_default), None)
        default_line = next((ln for ln in lines if ln.is_default), None)

        def _word(box: Box, order: Optional[int] = None) -> dict:
            cx, cy = box.x_center * img_w, box.y_center * img_h
            w, h = box.width * img_w, box.height * img_h
            d = {
                "polygon": [
                    [cx - w / 2, cy - h / 2],
                    [cx + w / 2, cy - h / 2],
                    [cx + w / 2, cy + h / 2],
                    [cx - w / 2, cy + h / 2],
                ],
                "detection_confidence": 1.0,
                "text": box.text,
                "recognition_confidence": 1.0,
            }
            if order is not None:
                d["order"] = order
            return d

        def _line(line: Line, order: Optional[int] = None) -> dict:
            words = []
            for idx, bid in enumerate(line.boxes):
                b = box_map.get(bid)
                if b:
                    words.append(_word(b, order=idx))
            d = {"words": words}
            if order is not None:
                d["order"] = order
            return d

        # Regular blocks (non-default)
        result_blocks = []
        bi = 0
        for block in blocks:
            if block.is_default:
                continue
            block_lines = []
            for li, lid in enumerate(block.lines):
                ln = line_map.get(lid)
                if ln and not ln.is_default:
                    block_lines.append(_line(ln, order=li))
            result_blocks.append(
                {"lines": block_lines, "words": [], "order": bi}
            )
            bi += 1

        # Free lines = non-default lines inside the default block
        free_lines = []
        if default_block:
            fi = 0
            for lid in default_block.lines:
                ln = line_map.get(lid)
                if ln and not ln.is_default:
                    free_lines.append(_line(ln, order=fi))
                    fi += 1

        # Free words = words inside the default line
        free_words = []
        if default_line:
            for i, bid in enumerate(default_line.boxes):
                b = box_map.get(bid)
                if b:
                    free_words.append(_word(b, order=i))

        return {
            "blocks": result_blocks,
            "free_lines": free_lines,
            "free_words": free_words,
        }

    # ------------------------------------------------------------------
    #  Import one page  (dict  →  DB)
    # ------------------------------------------------------------------

    @staticmethod
    def import_page(db: OCRDatabase, image_folder: str,
                    image_name: str, page_data: dict):
        """Write *page_data* into *db* for *image_name*.

        Uses a single raw connection for speed, then calls
        ``ensure_defaults`` to guarantee hierarchy.
        """
        img = QImage(os.path.join(image_folder, image_name))
        img_w, img_h = img.width(), img.height()
        if img_w == 0 or img_h == 0:
            return

        def _polygon_to_yolo(polygon):
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            return (
                (xmin + xmax) / 2 / img_w,
                (ymin + ymax) / 2 / img_h,
                (xmax - xmin) / img_w,
                (ymax - ymin) / img_h,
            )

        conn = sqlite3.connect(db.db_path)
        try:
            c = conn.cursor()

            # Ensure defaults exist inside this connection
            c.execute(
                "SELECT id FROM blocks "
                "WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            if row:
                default_block_id = row[0]
            else:
                c.execute(
                    "INSERT INTO blocks "
                    "(image_name, name, order_index, is_default) "
                    "VALUES (?, ?, 999999, 1)",
                    (image_name, "Нераспределённые"),
                )
                default_block_id = c.lastrowid

            c.execute(
                "SELECT id FROM lines "
                "WHERE image_name = ? AND is_default = 1",
                (image_name,),
            )
            row = c.fetchone()
            if row:
                default_line_id = row[0]
            else:
                c.execute(
                    "INSERT INTO lines "
                    "(image_name, text, created_at, order_index, "
                    "block_id, is_default) "
                    "VALUES (?, '', datetime('now'), 999999, ?, 1)",
                    (image_name, default_block_id),
                )
                default_line_id = c.lastrowid

            def _create_box(cx, cy, w, h, text, lid=None, order=0):
                target_line = lid if lid else default_line_id
                c.execute(
                    "INSERT INTO annotations "
                    "(image_name, x_center, y_center, width, height, "
                    "decoding, line_id, line_order) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (image_name, cx, cy, w, h, text, target_line, order),
                )
                return c.lastrowid

            def _create_line(box_ids, blk_id=None):
                target_block = blk_id if blk_id else default_block_id
                c.execute(
                    "INSERT INTO lines "
                    "(image_name, text, created_at, block_id, is_default) "
                    "VALUES (?, ?, datetime('now'), ?, 0)",
                    (image_name, "", target_block),
                )
                lid = c.lastrowid
                for order, bid in enumerate(box_ids):
                    c.execute(
                        "UPDATE annotations "
                        "SET line_id=?, line_order=? WHERE id=?",
                        (lid, order, bid),
                    )
                return lid

            def _create_block(name):
                c.execute(
                    "SELECT MAX(order_index) FROM blocks "
                    "WHERE image_name = ? AND is_default = 0",
                    (image_name,),
                )
                n = (c.fetchone()[0] or 0) + 1
                c.execute(
                    "INSERT INTO blocks "
                    "(image_name, name, order_index, is_default) "
                    "VALUES (?, ?, ?, 0)",
                    (image_name, name, n),
                )
                return c.lastrowid

            # --- Import blocks ---
            for block_data in page_data.get("blocks", []):
                lines_data = block_data.get("lines", [])
                block_id = (
                    _create_block("Блок") if len(lines_data) > 1 else None
                )
                for line_data in lines_data:
                    bids = []
                    for wd in line_data.get("words", []):
                        poly = wd.get("polygon", [])
                        if len(poly) >= 4:
                            bids.append(
                                _create_box(
                                    *_polygon_to_yolo(poly),
                                    wd.get("text", ""),
                                )
                            )
                    if bids:
                        lid = _create_line(bids, block_id)
                        if block_id:
                            c.execute(
                                "UPDATE lines SET block_id=? WHERE id=?",
                                (block_id, lid),
                            )

            # --- Import free lines → default block ---
            for line_data in page_data.get("free_lines", []):
                bids = []
                for wd in line_data.get("words", []):
                    poly = wd.get("polygon", [])
                    if len(poly) >= 4:
                        bids.append(
                            _create_box(
                                *_polygon_to_yolo(poly),
                                wd.get("text", ""),
                            )
                        )
                if bids:
                    _create_line(bids, default_block_id)

            # --- Import free words → default line ---
            for i, wd in enumerate(page_data.get("free_words", [])):
                poly = wd.get("polygon", [])
                if len(poly) >= 4:
                    _create_box(
                        *_polygon_to_yolo(poly),
                        wd.get("text", ""),
                        lid=default_line_id,
                        order=i,
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    #  COCO Export  →  {images, annotations, categories}
    # ------------------------------------------------------------------

    @staticmethod
    def build_coco(db: OCRDatabase, image_folder: str,
                   images_list: List[str]) -> dict:
        """Build a full COCO-format dict for all images."""
        coco_images = []
        coco_annotations = []
        ann_id = 1

        for img_idx, image_name in enumerate(images_list):
            img = QImage(os.path.join(image_folder, image_name))
            img_w, img_h = img.width(), img.height()
            if img_w == 0 or img_h == 0:
                continue

            image_id = img_idx + 1
            coco_images.append({
                "id": image_id,
                "file_name": image_name,
                "width": img_w,
                "height": img_h,
            })

            boxes = db.get_boxes(image_name)
            for box in boxes:
                # Convert normalized → absolute pixels
                cx_abs = box.x_center * img_w
                cy_abs = box.y_center * img_h
                w_abs = box.width * img_w
                h_abs = box.height * img_h
                x = cx_abs - w_abs / 2
                y = cy_abs - h_abs / 2

                coco_annotations.append({
                    "id": ann_id,
                    "image_id": image_id,
                    "category_id": 0,
                    "bbox": [round(x, 1), round(y, 1),
                             round(w_abs, 1), round(h_abs, 1)],
                    "area": round(w_abs * h_abs, 1),
                    "iscrowd": 0,
                    "attributes": {
                        "transcription": box.text or "",
                    },
                    "segmentation": [[
                        round(x, 1), round(y, 1),
                        round(x + w_abs, 1), round(y, 1),
                        round(x + w_abs, 1), round(y + h_abs, 1),
                        round(x, 1), round(y + h_abs, 1),
                    ]],
                })
                ann_id += 1

        return {
            "images": coco_images,
            "annotations": coco_annotations,
            "categories": [{"id": 0, "name": "class_0"}],
        }

    # ------------------------------------------------------------------
    #  COCO Import  (dict  →  DB)
    # ------------------------------------------------------------------

    @staticmethod
    def import_coco(db: OCRDatabase, image_folder: str,
                    coco_data: dict, folder_imgs: set):
        """Import COCO-format data into the database.

        All annotations become free words in the default line.
        """
        images = coco_data.get("images", [])
        annotations = coco_data.get("annotations", [])

        # Build image_id → file_name mapping
        id_to_name = {img["id"]: img["file_name"] for img in images}
        id_to_size = {
            img["id"]: (img.get("width", 0), img.get("height", 0))
            for img in images
        }

        # Group annotations by image_id
        anns_by_image: dict = {}
        for ann in annotations:
            iid = ann.get("image_id")
            if iid not in anns_by_image:
                anns_by_image[iid] = []
            anns_by_image[iid].append(ann)

        count = 0
        for image_id, file_name in id_to_name.items():
            if file_name not in folder_imgs:
                continue

            # Get image dimensions from COCO metadata or from file
            coco_w, coco_h = id_to_size.get(image_id, (0, 0))
            if coco_w == 0 or coco_h == 0:
                img = QImage(os.path.join(image_folder, file_name))
                coco_w, coco_h = img.width(), img.height()
            if coco_w == 0 or coco_h == 0:
                continue

            # Ensure defaults
            db.ensure_defaults(file_name)

            conn = sqlite3.connect(db.db_path)
            try:
                c = conn.cursor()

                # Get default line
                c.execute(
                    "SELECT id FROM lines "
                    "WHERE image_name = ? AND is_default = 1",
                    (file_name,),
                )
                default_line_id = c.fetchone()[0]

                image_anns = anns_by_image.get(image_id, [])
                for order, ann in enumerate(image_anns):
                    bbox = ann.get("bbox", [])
                    if len(bbox) < 4:
                        continue

                    bx, by, bw, bh = bbox
                    # Convert absolute pixels → normalized (0..1)
                    cx = (bx + bw / 2) / coco_w
                    cy = (by + bh / 2) / coco_h
                    w_norm = bw / coco_w
                    h_norm = bh / coco_h

                    text = ""
                    attrs = ann.get("attributes", {})
                    if isinstance(attrs, dict):
                        text = attrs.get("transcription", "")

                    c.execute(
                        "INSERT INTO annotations "
                        "(image_name, x_center, y_center, width, height, "
                        "decoding, line_id, line_order) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (file_name, cx, cy, w_norm, h_norm,
                         text, default_line_id, order),
                    )

                conn.commit()
                count += 1
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        return count
