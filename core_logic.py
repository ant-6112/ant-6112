import fitz
import uuid
import json
import os
import re
from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPainter


# --- Data Structures ---
class FieldExtractionDefinition:
    def __init__(
        self,
        field_id=None,
        label="",
        sub_type=None,
        extraction_scope=None,
        n_words=0,
        anchor_text=None,
        match_type="Exact Match",
        anchor_point=None,
        coordinate_box=None,
        above_below_tolerance_y=30,
        above_below_tolerance_x_factor=1.5,
    ):
        self.field_id = field_id if field_id else uuid.uuid4().hex[:12]
        self.label = label
        self.sub_type = sub_type
        self.extraction_scope = extraction_scope
        self.n_words = int(n_words) if n_words else 0
        self.anchor_text = anchor_text
        self.match_type = match_type
        self.anchor_point = anchor_point
        self.coordinate_box = coordinate_box
        self.above_below_tolerance_y = above_below_tolerance_y
        self.above_below_tolerance_x_factor = above_below_tolerance_x_factor

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        field_def = cls()
        data.pop("key_name", None)
        field_def.__dict__.update(data)
        field_def.n_words = int(field_def.n_words) if field_def.n_words else 0
        if "above_below_tolerance_y" not in data:
            field_def.above_below_tolerance_y = 45
        if "above_below_tolerance_x_factor" not in data:
            field_def.above_below_tolerance_x_factor = 1.5
        return field_def


class TemplateDefinition:
    def __init__(
        self,
        template_id=None,
        name="",
        identifying_keywords=None,
        test_pdf_path="",
        redaction_texts=None,
        field_definitions=None,
    ):
        self.template_id = template_id if template_id else uuid.uuid4().hex[:10].upper()
        self.name = name
        self.identifying_keywords = (
            identifying_keywords if identifying_keywords is not None else []
        )
        self.test_pdf_path = test_pdf_path
        self.redaction_texts = redaction_texts if redaction_texts is not None else []
        self.field_definitions = (
            field_definitions if field_definitions is not None else []
        )

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "name": self.name,
            "identifying_keywords": self.identifying_keywords,
            "test_pdf_path": self.test_pdf_path,
            "redaction_texts": self.redaction_texts,
            "field_definitions": [fd.to_dict() for fd in self.field_definitions],
        }

    @classmethod
    def from_dict(cls, data):
        template = cls(
            template_id=data.get("template_id"),
            name=data.get("name", ""),
            identifying_keywords=data.get("identifying_keywords", []),
            test_pdf_path=data.get("test_pdf_path", ""),
            redaction_texts=data.get("redaction_texts", []),
        )
        template.field_definitions = [
            FieldExtractionDefinition.from_dict(fd_data)
            for fd_data in data.get("field_definitions", [])
        ]
        return template


class ExtractedFieldResult:
    def __init__(
        self,
        template_id,
        field_id,
        field_label,
        extracted_text,
        source_pdf,
        source_page_idx,
        highlight_rects_pdf_coords=None,
        anchor_highlight_rects_pdf_coords=None,
    ):
        self.template_id = template_id
        self.field_id = field_id
        self.field_label = field_label
        self.extracted_text = extracted_text
        self.original_extracted_text = str(extracted_text)
        self.source_pdf = os.path.basename(source_pdf)
        self.source_pdf_full_path = source_pdf
        self.source_page_idx = source_page_idx
        self.highlight_rects_pdf_coords = (
            [tuple(r) for r in highlight_rects_pdf_coords]
            if highlight_rects_pdf_coords
            else []
        )
        self.anchor_highlight_rects_pdf_coords = (
            [tuple(r) for r in anchor_highlight_rects_pdf_coords]
            if anchor_highlight_rects_pdf_coords
            else []
        )

    def to_dict(self):
        d = self.__dict__.copy()
        if "source_pdf_full_path" in d:
            del d["source_pdf_full_path"]
        return d

    @classmethod
    def from_dict(cls, data):
        result = cls(
            template_id=data.get("template_id"),
            field_id=data.get("field_id"),
            field_label=data.get("field_label"),
            extracted_text=data.get("extracted_text"),
            source_pdf=data.get("source_pdf"),
            source_page_idx=data.get("source_page_idx"),
            highlight_rects_pdf_coords=data.get("highlight_rects_pdf_coords", []),
            anchor_highlight_rects_pdf_coords=data.get(
                "anchor_highlight_rects_pdf_coords", []
            ),
        )
        if "original_extracted_text" not in data:
            result.original_extracted_text = str(result.extracted_text)
        result.source_pdf_full_path = None
        return result


class DocumentRunReport:
    def __init__(
        self,
        run_id=None,
        timestamp=None,
        source_pdf_path=None,
        applied_template_id=None,
        results=None,
    ):
        self.run_id = run_id if run_id else uuid.uuid4().hex[:12]
        self.timestamp = (
            timestamp if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.source_pdf_path = source_pdf_path
        self.applied_template_id = applied_template_id
        self.field_results = results if results else []

    def add_field_result(self, result: ExtractedFieldResult):
        self.field_results.append(result)

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "source_pdf_path": os.path.basename(self.source_pdf_path)
            if self.source_pdf_path
            else None,
            "applied_template_id": self.applied_template_id,
            "field_results": [r.to_dict() for r in self.field_results],
        }

    @classmethod
    def from_dict(cls, data):
        report = cls(
            run_id=data.get("run_id"),
            timestamp=data.get("timestamp"),
            source_pdf_path=data.get("source_pdf_path"),
            applied_template_id=data.get("applied_template_id"),
        )
        report.field_results = [
            ExtractedFieldResult.from_dict(r_data)
            for r_data in data.get("field_results", [])
        ]
        return report


# --- Persistence (No change from previous) ---
TEMPLATES_FILE = "templates.json"
REPORTS_DIR = "doc_run_reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)


def save_templates(templates: list[TemplateDefinition]):
    with open(TEMPLATES_FILE, "w") as f:
        json.dump([t.to_dict() for t in templates], f, indent=4)


def load_templates():
    if not os.path.exists(TEMPLATES_FILE):
        return []
    try:
        with open(TEMPLATES_FILE, "r") as f:
            return [TemplateDefinition.from_dict(data) for data in json.load(f)]
    except json.JSONDecodeError:
        return []


def save_document_run_report(report: DocumentRunReport):
    pdf_name_part = (
        os.path.splitext(os.path.basename(report.source_pdf_path))[0]
        if report.source_pdf_path
        else "unknown_pdf"
    )
    template_part = (
        report.applied_template_id if report.applied_template_id else "no_template"
    )
    filename = f"report_{pdf_name_part}_{template_part}_{report.run_id}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(report.to_dict(), f, indent=4)


def load_document_run_reports() -> list[DocumentRunReport]:
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.startswith("report_") and filename.endswith(".json"):
            try:
                with open(os.path.join(REPORTS_DIR, filename), "r") as f:
                    reports.append(DocumentRunReport.from_dict(json.load(f)))
            except Exception as e:
                print(f"Error loading document run report {filename}: {e}")
    reports.sort(key=lambda r: r.timestamp, reverse=True)
    return reports


# --- PDF Extraction Logic ---
class PDFProcessor:
    def __init__(self, pdf_path=None):
        self.pdf_path = pdf_path
        self.doc = None
        if pdf_path:
            self.load_pdf(pdf_path)

    def load_pdf(self, pdf_path):
        self.close()
        self.pdf_path = pdf_path
        if pdf_path and os.path.exists(pdf_path):
            try:
                self.doc = fitz.open(pdf_path)
            except Exception as e:
                print(f"Error opening PDF {pdf_path}: {e}")
                self.doc = None
        else:
            self.doc = None
            if pdf_path:
                print(f"PDF path does not exist: {pdf_path}")

    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None
        self.pdf_path = None

    def get_page_count(self):
        return self.doc.page_count if self.doc else 0

    def get_page_object(self, page_idx):
        if not self.doc or not (0 <= page_idx < self.doc.page_count):
            return None
        return self.doc.load_page(page_idx)

    def get_page_pixmap(self, page_idx, zoom=2.0, redaction_texts=None):
        page = self.get_page_object(page_idx)
        if not page:
            return None
        mat = fitz.Matrix(zoom, zoom)
        try:
            pix = page.get_pixmap(matrix=mat, alpha=False)
        except RuntimeError:
            pix = page.get_pixmap(matrix=mat, alpha=True)
        if redaction_texts and PYMUPDF_SUPPORTS_REDACT_ANNOT:
            from PyQt5.QtGui import QImage, QPainter, QColor
            from PyQt5.QtCore import Qt, QRectF

            qimage_format = (
                QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            )
            temp_qimage = QImage(
                pix.samples, pix.width, pix.height, pix.stride, qimage_format
            ).copy()
            painter = QPainter(temp_qimage)
            painter.setBrush(Qt.black)
            painter.setPen(Qt.black)
            for text_to_redact in redaction_texts:
                if not text_to_redact:
                    continue
                try:
                    for r_pdf in page.search_for(text_to_redact):
                        painter.drawRect(QRectF(*(r_pdf * mat)))
                except Exception as e:
                    print(f"Pixmap redaction error for '{text_to_redact}': {e}")
            painter.end()
            return temp_qimage
        return pix

    def _get_words_on_page(self, page: fitz.Page, sort_by_reading_order=True):
        if not page:
            return []
        words = page.get_text("words")
        if sort_by_reading_order:
            words.sort(key=lambda w: (w[5], w[6], w[7]))
        return words

    def _rect_contains_point(self, rect: fitz.Rect, px, py):
        return rect.x0 <= px <= rect.x1 and rect.y0 <= py <= rect.y1

    def _find_anchor_instances(
        self, page: fitz.Page, words_on_page: list, anchor_text: str, match_type: str
    ) -> list[fitz.Rect]:
        found_instances = []
        if not anchor_text:
            return found_instances
        if match_type == "Exact Match":
            found_instances = page.search_for(anchor_text)
        elif match_type == "Case Insensitive":
            if PYMUPDF_NEW_ENOUGH_FOR_FLAGS:
                try:
                    found_instances = page.search_for(
                        anchor_text, flags=fitz.TEXT_SEARCH_CASE_INSENSITIVE
                    )
                except AttributeError:
                    found_instances = [
                        fitz.Rect(w[:4])
                        for w in words_on_page
                        if anchor_text.lower() in w[4].lower()
                    ]
            else:
                found_instances = [
                    fitz.Rect(w[:4])
                    for w in words_on_page
                    if anchor_text.lower() in w[4].lower()
                ]
        elif match_type == "Regular Expression":
            try:
                regex = re.compile(anchor_text)
                for w_tuple in words_on_page:
                    if regex.search(w_tuple[4]):
                        found_instances.append(fitz.Rect(w_tuple[:4]))
            except re.error as e:
                print(f"Invalid regex '{anchor_text}': {e}")
        return found_instances

    def _get_expanded_text_above_below(
        self,
        page: fitz.Page,
        words_on_page: list,
        base_rect: fitz.Rect,
        direction: str,
        tolerance_y: int,
        tolerance_x_factor: float,
    ) -> tuple[str, list[tuple]]:
        extracted_text = ""
        highlight_word_coords = []
        page_bounds = page.rect
        exp_x0 = max(
            page_bounds.x0,
            base_rect.x0 - (base_rect.width * (tolerance_x_factor - 1) / 2),
        )
        exp_x1 = min(
            page_bounds.x1,
            base_rect.x1 + (base_rect.width * (tolerance_x_factor - 1) / 2),
        )
        if direction == "above":
            s_y0 = max(page_bounds.y0, base_rect.y0 - tolerance_y)
            s_y1 = max(page_bounds.y0, base_rect.y0 - 1)
        elif direction == "below":
            s_y0 = min(page_bounds.y1, base_rect.y1 + 1)
            s_y1 = min(page_bounds.y1, base_rect.y1 + tolerance_y)
        else:
            return "", []
        if s_y0 >= s_y1:
            return "", []
        search_rect = fitz.Rect(exp_x0, s_y0, exp_x1, s_y1)
        cand_words = sorted(
            [w for w in words_on_page if search_rect.intersects(fitz.Rect(w[:4]))],
            key=lambda w: (w[1], w[0]),
        )
        if not cand_words:
            return "", []
        extracted_text = " ".join([w[4] for w in cand_words])
        highlight_word_coords = [tuple(fitz.Rect(w[:4])) for w in cand_words]
        return extracted_text.strip(), highlight_word_coords

    def extract_field_data(
        self, field_def: FieldExtractionDefinition, page_idx: int
    ) -> ExtractedFieldResult:
        page = self.get_page_object(page_idx)
        if not page:
            return ExtractedFieldResult(
                None,
                field_def.field_id,
                field_def.label,
                "[ERROR: Page not loaded]",
                self.pdf_path,
                page_idx,
            )

        words_on_page = self._get_words_on_page(page)
        extracted_text = ""
        highlight_rects_pdf_tuples = []
        anchor_highlight_rects_pdf_tuples = []

        try:
            if field_def.sub_type == "Coordinate Box":
                if field_def.coordinate_box:
                    rect = fitz.Rect(field_def.coordinate_box)
                    extracted_text = page.get_text("text", clip=rect).strip()
                    highlight_rects_pdf_tuples.append(tuple(rect))

            elif field_def.sub_type == "Anchor Word":
                found_anchor_fitz_rects = self._find_anchor_instances(
                    page, words_on_page, field_def.anchor_text, field_def.match_type
                )

                if found_anchor_fitz_rects:
                    anchor_rect_obj = found_anchor_fitz_rects[
                        0
                    ]  # Use the first found anchor
                    anchor_highlight_rects_pdf_tuples.append(tuple(anchor_rect_obj))

                    # Words that constitute the found anchor phrase itself
                    current_anchor_words = [
                        w
                        for w in words_on_page
                        if anchor_rect_obj.intersects(fitz.Rect(w[:4]))
                    ]
                    if not current_anchor_words:  # Fallback if intersect fails (e.g. anchor is a tiny part of a word)
                        current_anchor_words = [
                            w
                            for w in words_on_page
                            if anchor_rect_obj.contains(fitz.Rect(w[:4]).tl)
                        ]
                    if (
                        not current_anchor_words and words_on_page
                    ):  # Last resort, find closest word to anchor_rect center
                        anchor_center_x = (anchor_rect_obj.x0 + anchor_rect_obj.x1) / 2
                        anchor_center_y = (anchor_rect_obj.y0 + anchor_rect_obj.y1) / 2
                        closest_w = min(
                            words_on_page,
                            key=lambda w: (
                                ((w[0] + w[2]) / 2 - anchor_center_x) ** 2
                                + ((w[1] + w[3]) / 2 - anchor_center_y) ** 2
                            ),
                        )
                        current_anchor_words = [closest_w]

                    if current_anchor_words:
                        ref_word_info = current_anchor_words[
                            0
                        ]  # First word of the (potentially multi-word) anchor
                        anchor_block_no, anchor_line_no = (
                            ref_word_info[5],
                            ref_word_info[6],
                        )

                        # Get all words on the same logical line as the anchor's first word
                        words_on_anchor_line = sorted(
                            [
                                w
                                for w in words_on_page
                                if w[5] == anchor_block_no and w[6] == anchor_line_no
                            ],
                            key=lambda w: w[7],
                        )

                        # Find the index of the first word of the anchor phrase in this line
                        first_anchor_word_idx_in_line = 0
                        for i, lw in enumerate(words_on_anchor_line):
                            if (
                                lw[0] == ref_word_info[0]
                                and lw[1] == ref_word_info[1]
                                and lw[4] == ref_word_info[4]
                            ):  # Match by coord and text
                                first_anchor_word_idx_in_line = i
                                break

                        # Find the index of the last word of the anchor phrase in this line
                        last_anchor_word_of_phrase = current_anchor_words[-1]
                        last_anchor_word_idx_in_line = first_anchor_word_idx_in_line  # Default to first if only one word anchor
                        for i in range(
                            first_anchor_word_idx_in_line, len(words_on_anchor_line)
                        ):
                            lw = words_on_anchor_line[i]
                            # Check if lw is the last word of the anchor phrase
                            if (
                                lw[0] == last_anchor_word_of_phrase[0]
                                and lw[1] == last_anchor_word_of_phrase[1]
                                and lw[4] == last_anchor_word_of_phrase[4]
                            ):
                                last_anchor_word_idx_in_line = i
                                break  # Found the end of the anchor phrase
                            # If current_anchor_words has more words, ensure we are not breaking early
                            if len(current_anchor_words) > (
                                i - first_anchor_word_idx_in_line + 1
                            ):
                                next_anchor_word_in_phrase = current_anchor_words[
                                    i - first_anchor_word_idx_in_line + 1
                                ]
                                if not (
                                    lw[0] == next_anchor_word_in_phrase[0]
                                    and lw[1] == next_anchor_word_in_phrase[1]
                                    and lw[4] == next_anchor_word_in_phrase[4]
                                ):
                                    # This line word is not part of the anchor phrase anymore
                                    last_anchor_word_idx_in_line = (
                                        i - 1
                                    )  # previous one was the last
                                    break
                            elif (
                                i == len(words_on_anchor_line) - 1
                            ):  # Reached end of line, current word is last of anchor
                                last_anchor_word_idx_in_line = i

                        if (
                            last_anchor_word_idx_in_line < first_anchor_word_idx_in_line
                        ):  # Sanity check
                            last_anchor_word_idx_in_line = first_anchor_word_idx_in_line

                        target_word_objects = []
                        if field_def.extraction_scope == "Whole Line":
                            target_word_objects = words_on_anchor_line
                        elif field_def.extraction_scope == "Next N Words (Right)":
                            start_idx = last_anchor_word_idx_in_line + 1
                            target_word_objects = words_on_anchor_line[
                                start_idx : start_idx + field_def.n_words
                            ]
                        elif field_def.extraction_scope == "Previous N Words (Left)":
                            end_idx = first_anchor_word_idx_in_line
                            target_word_objects = words_on_anchor_line[
                                max(0, end_idx - field_def.n_words) : end_idx
                            ]
                        elif field_def.extraction_scope == "Text above the Word":
                            extracted_text, highlight_coords_tuples = (
                                self._get_expanded_text_above_below(
                                    page,
                                    words_on_page,
                                    anchor_rect_obj,
                                    "above",
                                    field_def.above_below_tolerance_y,
                                    field_def.above_below_tolerance_x_factor,
                                )
                            )
                            highlight_rects_pdf_tuples.extend(highlight_coords_tuples)
                        elif field_def.extraction_scope == "Text below the Word":
                            extracted_text, highlight_coords_tuples = (
                                self._get_expanded_text_above_below(
                                    page,
                                    words_on_page,
                                    anchor_rect_obj,
                                    "below",
                                    field_def.above_below_tolerance_y,
                                    field_def.above_below_tolerance_x_factor,
                                )
                            )
                            highlight_rects_pdf_tuples.extend(highlight_coords_tuples)
                        elif field_def.extraction_scope == "Value After Anchor (Line)":
                            # Value is all words on the same line AFTER the last word of the anchor
                            if (
                                last_anchor_word_idx_in_line
                                < len(words_on_anchor_line) - 1
                            ):
                                target_word_objects = words_on_anchor_line[
                                    last_anchor_word_idx_in_line + 1 :
                                ]
                        elif (
                            field_def.extraction_scope
                            == "Value After Anchor (Next N Words)"
                        ):
                            # Value is N words on the same line AFTER the last word of the anchor
                            if (
                                last_anchor_word_idx_in_line
                                < len(words_on_anchor_line) - 1
                            ):
                                start_idx = last_anchor_word_idx_in_line + 1
                                target_word_objects = words_on_anchor_line[
                                    start_idx : start_idx + field_def.n_words
                                ]

                        if (
                            target_word_objects
                        ):  # Common processing for word-based results
                            extracted_text = " ".join(
                                [w[4] for w in target_word_objects]
                            )
                            highlight_rects_pdf_tuples.extend(
                                [tuple(fitz.Rect(w[:4])) for w in target_word_objects]
                            )

            elif field_def.sub_type == "Anchor Point":
                if field_def.anchor_point:
                    px, py = field_def.anchor_point
                    anchor_highlight_rects_pdf_tuples.append(
                        (px - 1, py - 1, px + 1, py + 1)
                    )  # Tiny marker for the point

                    ref_word_info = None
                    min_dist_sq = float("inf")
                    for w_tuple in words_on_page:
                        w_rect = fitz.Rect(w_tuple[:4])
                        contained = (
                            self._rect_contains_point(w_rect, px, py)
                            if not PYMUPDF_HAS_CONTAINS_POINT
                            else w_rect.contains_point(px, py)
                        )
                        if contained:
                            ref_word_info = w_tuple
                            break

                        center_x, center_y = (0, 0)  # Initialize
                        if PYMUPDF_HAS_RECT_CENTER:
                            center_x, center_y = w_rect.center
                        else:
                            center_x, center_y = (
                                (w_rect.x0 + w_rect.x1) / 2,
                                (w_rect.y0 + w_rect.y1) / 2,
                            )

                        dist_sq = (px - center_x) ** 2 + (py - center_y) ** 2
                        if dist_sq < min_dist_sq:
                            min_dist_sq = dist_sq
                            ref_word_info = w_tuple

                    if ref_word_info:
                        anchor_highlight_rects_pdf_tuples.append(
                            tuple(fitz.Rect(ref_word_info[:4]))
                        )

                        target_word_objects = []
                        ref_rect_obj = fitz.Rect(ref_word_info[:4])
                        if field_def.extraction_scope == "Next N Words (Right)":
                            y_mid_ref = (ref_rect_obj.y0 + ref_rect_obj.y1) / 2
                            y_tol = ref_rect_obj.height / 1.5  # Adjusted tolerance
                            cand_right = sorted(
                                [
                                    w
                                    for w in words_on_page
                                    if fitz.Rect(w[:4]).x0 > ref_rect_obj.x0
                                    and abs(
                                        (
                                            (fitz.Rect(w[:4]).y0 + fitz.Rect(w[:4]).y1)
                                            / 2
                                        )
                                        - y_mid_ref
                                    )
                                    <= y_tol
                                ],
                                key=lambda w: w[0],
                            )
                            # Filter further: only take words whose x0 is greater than ref_word's x1 (strictly right)
                            cand_right_strict = [
                                w
                                for w in cand_right
                                if fitz.Rect(w[:4]).x0 > ref_rect_obj.x1
                            ]
                            target_word_objects = cand_right_strict[: field_def.n_words]
                        elif field_def.extraction_scope == "Previous N Words (Left)":
                            y_mid_ref = (ref_rect_obj.y0 + ref_rect_obj.y1) / 2
                            y_tol = ref_rect_obj.height / 1.5
                            cand_left = sorted(
                                [
                                    w
                                    for w in words_on_page
                                    if fitz.Rect(w[:4]).x1 < ref_rect_obj.x1
                                    and abs(
                                        (
                                            (fitz.Rect(w[:4]).y0 + fitz.Rect(w[:4]).y1)
                                            / 2
                                        )
                                        - y_mid_ref
                                    )
                                    <= y_tol
                                ],
                                key=lambda w: w[0],
                                reverse=True,
                            )
                            cand_left_strict = [
                                w
                                for w in cand_left
                                if fitz.Rect(w[:4]).x1 < ref_rect_obj.x0
                            ]
                            target_word_objects = cand_left_strict[: field_def.n_words]
                            target_word_objects.reverse()
                        elif (
                            field_def.extraction_scope == "Whole Line"
                        ):  # Line containing the ref_word_info based on block/line numbers
                            target_word_objects = sorted(
                                [
                                    w
                                    for w in words_on_page
                                    if w[5] == ref_word_info[5]
                                    and w[6] == ref_word_info[6]
                                ],
                                key=lambda w: w[7],
                            )
                        elif field_def.extraction_scope == "Text at/on the Point":
                            target_word_objects = [ref_word_info]
                        elif field_def.extraction_scope == "Text above the Point":
                            extracted_text, hl_coords = (
                                self._get_expanded_text_above_below(
                                    page,
                                    words_on_page,
                                    ref_rect_obj,
                                    "above",
                                    field_def.above_below_tolerance_y,
                                    field_def.above_below_tolerance_x_factor,
                                )
                            )
                            highlight_rects_pdf_tuples.extend(hl_coords)
                        elif field_def.extraction_scope == "Text below the Point":
                            extracted_text, hl_coords = (
                                self._get_expanded_text_above_below(
                                    page,
                                    words_on_page,
                                    ref_rect_obj,
                                    "below",
                                    field_def.above_below_tolerance_y,
                                    field_def.above_below_tolerance_x_factor,
                                )
                            )
                            highlight_rects_pdf_tuples.extend(hl_coords)

                        if target_word_objects:
                            extracted_text = " ".join(
                                [w[4] for w in target_word_objects]
                            )
                            highlight_rects_pdf_tuples.extend(
                                [tuple(fitz.Rect(w[:4])) for w in target_word_objects]
                            )

        except Exception as e:
            error_message = f"[ERROR ({field_def.sub_type} - {field_def.extraction_scope or ''}): {e}]"
            print(
                f"Error extracting field '{field_def.label}': {error_message}\nTraceback: {traceback.format_exc()}"
            )
            extracted_text = error_message

        return ExtractedFieldResult(
            template_id=None,
            field_id=field_def.field_id,
            field_label=field_def.label,
            extracted_text=extracted_text.strip(),
            source_pdf=self.pdf_path,
            source_page_idx=page_idx,
            highlight_rects_pdf_coords=highlight_rects_pdf_tuples,
            anchor_highlight_rects_pdf_coords=anchor_highlight_rects_pdf_tuples,
        )

    def detect_document_type(
        self, page_idx: int, templates: list[TemplateDefinition]
    ) -> TemplateDefinition | None:
        # ... (This method remains the same as previous version)
        page = self.get_page_object(page_idx)
        if not page:
            return None
        page_text_lower = page.get_text("text").lower()
        for template in templates:
            if not template.identifying_keywords:
                continue
            match_count = sum(
                1
                for keyword in template.identifying_keywords
                if keyword.lower() in page_text_lower
            )
            if template.identifying_keywords and match_count == len(
                template.identifying_keywords
            ):
                return template
        return None

    def get_redaction_rects_for_page(
        self, page_idx: int, redaction_texts: list[str]
    ) -> list[tuple]:
        page = self.get_page_object(page_idx)
        if not page or not redaction_texts:
            return []
        all_redact_rects_tuples = []
        if PYMUPDF_SUPPORTS_REDACT_ANNOT:
            for text_to_redact in redaction_texts:
                if not text_to_redact.strip():
                    continue
                try:
                    for inst_rect in page.search_for(text_to_redact):
                        all_redact_rects_tuples.append(
                            tuple(inst_rect)
                        )  # Convert to tuple
                except Exception as e:
                    print(f"Error searching for redaction text '{text_to_redact}': {e}")
        return all_redact_rects_tuples
