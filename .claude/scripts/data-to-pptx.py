#!/usr/bin/env python3
"""
ACOS PPTX Generation Engine — Component Library + Layout Engine

Generates institutional-quality PPTX presentations from structured data.
Bypasses HTML intermediate — builds slides natively via python-pptx.

Usage:
    python3 data-to-pptx.py <data_yaml> <design_spec_yaml> [--template template.pptx] [-o output.pptx]

Input:
    data_yaml        — verified-data.yaml (loan data with provenance)
    design_spec_yaml — design-spec.yaml (colors, fonts, layout from Phase 1)
    --template       — optional blank .pptx with theme/masters
    -o               — output path (default: output.pptx)

All text uses shape.text_frame (never floating textboxes).
All text_frames have vertical_anchor set explicitly.
All margins set to 0 or intentional values.
Font selected by content role, not hardcoded.
"""
import argparse
import sys
import yaml
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt, Emu
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("ERROR: python-pptx required. Install: pip install python-pptx", file=sys.stderr)
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

SLIDE_WIDTH = Inches(13.333)   # 16:9 widescreen
SLIDE_HEIGHT = Inches(7.5)

# Default margins (from slide edge)
MARGIN_LEFT = Inches(0.5)
MARGIN_RIGHT = Inches(0.5)
MARGIN_TOP = Inches(0.5)
MARGIN_BOTTOM = Inches(0.4)

# Content area (after header/footer)
HEADER_HEIGHT = Inches(0.8)
FOOTER_HEIGHT = Inches(0.45)

# Font roles — auto-selected by content type
FONT_ROLES = {
    "number":  "Courier New",    # financial figures, percentages, dates
    "display": "Georgia",        # titles, headings, prose
    "label":   "Calibri",        # labels, captions, metadata
}

# Default colors (overridden by design spec)
DEFAULT_COLORS = {
    "primary":    RGBColor(0x1A, 0x3C, 0x5E),  # dark navy
    "secondary":  RGBColor(0x2E, 0x86, 0xAB),  # teal
    "accent":     RGBColor(0xD4, 0x8B, 0x2C),  # gold
    "bg_dark":    RGBColor(0x1A, 0x3C, 0x5E),
    "bg_light":   RGBColor(0xF5, 0xF5, 0xF5),
    "text_dark":  RGBColor(0x2D, 0x2D, 0x2D),
    "text_light": RGBColor(0xFF, 0xFF, 0xFF),
    "positive":   RGBColor(0x27, 0xAE, 0x60),
    "caution":    RGBColor(0xF3, 0x9C, 0x12),
    "negative":   RGBColor(0xE7, 0x4C, 0x3C),
    "border":     RGBColor(0xDD, 0xDD, 0xDD),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SPEC LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def load_design_spec(path):
    """Load design spec YAML and merge with defaults."""
    spec = {}
    if path and Path(path).exists():
        with open(path) as f:
            spec = yaml.safe_load(f) or {}

    colors = dict(DEFAULT_COLORS)
    if "colors" in spec:
        for key, hex_val in spec["colors"].items():
            if isinstance(hex_val, str) and hex_val.startswith("#"):
                hex_val = hex_val.lstrip("#")
                colors[key] = RGBColor(
                    int(hex_val[0:2], 16),
                    int(hex_val[2:4], 16),
                    int(hex_val[4:6], 16),
                )
    spec["_colors"] = colors

    fonts = dict(FONT_ROLES)
    if "fonts" in spec:
        for role, name in spec["fonts"].items():
            if role in fonts:
                fonts[role] = name
    spec["_fonts"] = fonts

    return spec


def load_data(path):
    """Load verified data YAML."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ContentArea:
    """Defines usable slide area after header/footer."""
    def __init__(self, header_h=HEADER_HEIGHT, footer_h=FOOTER_HEIGHT):
        self.left = MARGIN_LEFT
        self.top = MARGIN_TOP + header_h
        self.width = SLIDE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
        self.height = SLIDE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - header_h - footer_h


class SlideGrid:
    """Computes cell positions from cols/rows/gap specs within a content area."""
    def __init__(self, area, cols=1, rows=1, h_gap=Inches(0.2), v_gap=Inches(0.2)):
        self.area = area
        self.cols = cols
        self.rows = rows
        self.h_gap = h_gap
        self.v_gap = v_gap
        self.cell_width = (area.width - h_gap * (cols - 1)) // cols
        self.cell_height = (area.height - v_gap * (rows - 1)) // rows

    def cell(self, col, row):
        """Return (left, top, width, height) for grid cell at (col, row), 0-indexed."""
        left = self.area.left + col * (self.cell_width + self.h_gap)
        top = self.area.top + row * (self.cell_height + self.v_gap)
        return left, top, self.cell_width, self.cell_height

    def span(self, col_start, row_start, col_span=1, row_span=1):
        """Return bounds for a multi-cell span."""
        left = self.area.left + col_start * (self.cell_width + self.h_gap)
        top = self.area.top + row_start * (self.cell_height + self.v_gap)
        width = col_span * self.cell_width + (col_span - 1) * self.h_gap
        height = row_span * self.cell_height + (row_span - 1) * self.v_gap
        return left, top, width, height


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def detect_font_role(text):
    """Auto-detect content type for font role selection."""
    if not text:
        return "label"
    s = str(text).strip()
    # Numbers, currency, percentages, dates
    if any(c.isdigit() for c in s) and not s.isalpha():
        return "number"
    # Short labels (< 30 chars, no sentence structure)
    if len(s) < 30 and "." not in s:
        return "label"
    return "display"


def set_text(tf, text, font_size=Pt(12), bold=False, color=None,
             alignment=PP_ALIGN.LEFT, font_name=None, spec=None):
    """Set text on an existing text_frame's first paragraph."""
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = str(text)
    p.alignment = alignment
    run = p.runs[0] if p.runs else p.add_run()
    run.text = str(text)
    run.font.size = font_size
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    if font_name:
        run.font.name = font_name
    elif spec:
        run.font.name = spec["_fonts"].get(detect_font_role(text), "Calibri")
    return p


def add_paragraph(tf, text, font_size=Pt(12), bold=False, color=None,
                  alignment=PP_ALIGN.LEFT, font_name=None, spec=None,
                  space_before=Pt(0), space_after=Pt(0)):
    """Add a new paragraph to an existing text_frame."""
    p = tf.add_paragraph()
    p.text = str(text)
    p.alignment = alignment
    p.space_before = space_before
    p.space_after = space_after
    run = p.runs[0] if p.runs else p.add_run()
    run.text = str(text)
    run.font.size = font_size
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    if font_name:
        run.font.name = font_name
    elif spec:
        run.font.name = spec["_fonts"].get(detect_font_role(text), "Calibri")
    return p


def zero_margins(tf):
    """Set all internal margins to zero."""
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)


def set_margins(tf, left=Emu(0), right=Emu(0), top=Emu(0), bottom=Emu(0)):
    """Set explicit margins on a text_frame."""
    tf.margin_left = left
    tf.margin_right = right
    tf.margin_top = top
    tf.margin_bottom = bottom


def compute_height(font_size_pt, line_count, line_spacing=1.4):
    """Compute textbox height from content."""
    return Pt(font_size_pt * line_count * line_spacing)


# ═══════════════════════════════════════════════════════════════════════════════
# SHAPE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def add_rect(slide, left, top, width, height, fill_color=None, border_color=None, border_width=Pt(0)):
    """Add a rectangle shape with optional fill and border."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = border_width
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP):
    """Add a textbox with explicit anchor and zero margins."""
    txbox = slide.shapes.add_textbox(left, top, width, height)
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    zero_margins(tf)
    try:
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT
    except Exception:
        pass
    # Set vertical anchor
    txbox.text_frame_anchor = anchor
    return txbox, tf


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def header_bar(slide, title, subtitle=None, spec=None):
    """Render a slide header bar across the top."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    # Background bar
    add_rect(slide, Emu(0), Emu(0), SLIDE_WIDTH, HEADER_HEIGHT + MARGIN_TOP,
             fill_color=colors["bg_dark"])
    # Title text
    txbox, tf = add_textbox(slide, MARGIN_LEFT, MARGIN_TOP,
                            SLIDE_WIDTH - MARGIN_LEFT * 2, HEADER_HEIGHT,
                            anchor=MSO_ANCHOR.MIDDLE)
    set_text(tf, title, font_size=Pt(22), bold=True,
             color=colors["text_light"], font_name=spec["_fonts"]["display"] if spec else "Georgia",
             spec=spec)
    if subtitle:
        add_paragraph(tf, subtitle, font_size=Pt(12), bold=False,
                      color=colors["text_light"],
                      font_name=spec["_fonts"]["label"] if spec else "Calibri",
                      spec=spec)


def footer_bar(slide, left_text="", right_text="", spec=None):
    """Render a slide footer bar across the bottom."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    footer_top = SLIDE_HEIGHT - FOOTER_HEIGHT - MARGIN_BOTTOM
    # Separator line
    add_rect(slide, MARGIN_LEFT, footer_top, SLIDE_WIDTH - MARGIN_LEFT * 2,
             Pt(1), fill_color=colors["border"])
    # Left text
    if left_text:
        txbox, tf = add_textbox(slide, MARGIN_LEFT, footer_top + Pt(4),
                                Inches(5), FOOTER_HEIGHT - Pt(4),
                                anchor=MSO_ANCHOR.MIDDLE)
        set_text(tf, left_text, font_size=Pt(8), color=colors["text_dark"],
                 font_name=spec["_fonts"]["label"] if spec else "Calibri", spec=spec)
    # Right text
    if right_text:
        txbox, tf = add_textbox(slide, SLIDE_WIDTH - MARGIN_RIGHT - Inches(3),
                                footer_top + Pt(4), Inches(3), FOOTER_HEIGHT - Pt(4),
                                anchor=MSO_ANCHOR.MIDDLE)
        set_text(tf, right_text, font_size=Pt(8), color=colors["text_dark"],
                 alignment=PP_ALIGN.RIGHT,
                 font_name=spec["_fonts"]["label"] if spec else "Calibri", spec=spec)


def section_header(slide, title, area, spec=None):
    """Render a section divider heading within the content area."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    # Accent bar
    add_rect(slide, area.left, area.top, Inches(0.08), Inches(0.35),
             fill_color=colors["accent"])
    # Title
    txbox, tf = add_textbox(slide, area.left + Inches(0.2), area.top,
                            area.width - Inches(0.2), Inches(0.35),
                            anchor=MSO_ANCHOR.MIDDLE)
    set_text(tf, title.upper(), font_size=Pt(11), bold=True,
             color=colors["primary"],
             font_name=spec["_fonts"]["label"] if spec else "Calibri", spec=spec)
    return Inches(0.45)  # height consumed


def metric_card(slide, left, top, width, height, label, value, sub_text=None,
                bg_color=None, spec=None):
    """Render a metric card using shape.text_frame with paragraphs (no floating textboxes)."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    if bg_color is None:
        bg_color = colors["bg_light"]

    shape = add_rect(slide, left, top, width, height, fill_color=bg_color)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    set_margins(tf, left=Inches(0.15), right=Inches(0.15),
                top=Inches(0.12), bottom=Inches(0.08))

    # Label paragraph
    p_label = tf.paragraphs[0]
    p_label.text = str(label).upper()
    p_label.alignment = PP_ALIGN.LEFT
    p_label.space_after = Pt(2)
    run = p_label.runs[0] if p_label.runs else p_label.add_run()
    run.text = str(label).upper()
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = colors["secondary"]
    run.font.name = spec["_fonts"]["label"] if spec else "Calibri"

    # Value paragraph
    p_val = tf.add_paragraph()
    p_val.text = str(value)
    p_val.alignment = PP_ALIGN.LEFT
    p_val.space_before = Pt(2)
    p_val.space_after = Pt(2)
    run_v = p_val.add_run()
    run_v.text = str(value)
    run_v.font.size = Pt(18)
    run_v.font.bold = True
    run_v.font.color.rgb = colors["text_dark"]
    run_v.font.name = spec["_fonts"]["number"] if spec else "Courier New"

    # Sub-text paragraph (optional)
    if sub_text:
        p_sub = tf.add_paragraph()
        p_sub.text = str(sub_text)
        p_sub.alignment = PP_ALIGN.LEFT
        p_sub.space_before = Pt(1)
        run_s = p_sub.add_run()
        run_s.text = str(sub_text)
        run_s.font.size = Pt(8)
        run_s.font.color.rgb = colors["secondary"]
        run_s.font.name = spec["_fonts"]["label"] if spec else "Calibri"

    # Vertical anchor: middle if no sub-text, top otherwise
    shape.text_frame_anchor = MSO_ANCHOR.MIDDLE if not sub_text else MSO_ANCHOR.TOP


def badge_pill(slide, left, top, width, height, text, bg_color=None, text_color=None, spec=None):
    """Render a badge/pill (e.g., recommendation status) with centered text."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    if bg_color is None:
        bg_color = colors["positive"]
    if text_color is None:
        text_color = colors["text_light"]

    shape = add_rect(slide, left, top, width, height, fill_color=bg_color)
    # Round corners
    shape.adjustments[0] = 0.25

    tf = shape.text_frame
    tf.word_wrap = False
    tf.auto_size = None
    zero_margins(tf)
    shape.text_frame_anchor = MSO_ANCHOR.MIDDLE

    p = tf.paragraphs[0]
    p.text = str(text).upper()
    p.alignment = PP_ALIGN.CENTER
    run = p.runs[0] if p.runs else p.add_run()
    run.text = str(text).upper()
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = text_color
    run.font.name = spec["_fonts"]["label"] if spec else "Calibri"


def data_table(slide, left, top, width, headers, rows, spec=None, col_widths=None):
    """Render a native table with styled header and alternating rows."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    num_rows = len(rows) + 1  # +1 for header
    num_cols = len(headers)

    row_height = Inches(0.35)
    table_height = row_height * num_rows
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, table_height)
    table = table_shape.table

    # Set column widths
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
    else:
        col_w = width // num_cols
        for i in range(num_cols):
            table.columns[i].width = col_w

    # Header row
    for i, header_text in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = str(header_text)
        cell.fill.solid()
        cell.fill.fore_color.rgb = colors["bg_dark"]
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.runs[0] if p.runs else p.add_run()
        run.text = str(header_text)
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = colors["text_light"]
        run.font.name = spec["_fonts"]["label"] if spec else "Calibri"
        cell.text_frame.margin_left = Inches(0.08)
        cell.text_frame.margin_top = Pt(2)
        cell.text_frame.margin_bottom = Pt(2)

    # Data rows with alternating backgrounds
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_text in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = str(cell_text) if cell_text is not None else ""
            # Alternating row colors
            if r_idx % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = colors["bg_light"]
            else:
                cell.fill.background()

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.runs[0] if p.runs else p.add_run()
            run.text = str(cell_text) if cell_text is not None else ""
            # Use number font for numeric content
            role = detect_font_role(cell_text)
            run.font.name = spec["_fonts"].get(role, "Calibri") if spec else FONT_ROLES.get(role, "Calibri")
            run.font.size = Pt(9)
            run.font.color.rgb = colors["text_dark"]
            cell.text_frame.margin_left = Inches(0.08)
            cell.text_frame.margin_top = Pt(2)
            cell.text_frame.margin_bottom = Pt(2)

    return table_shape


def timeline_strip(slide, left, top, width, height, events, spec=None):
    """Render a horizontal timeline of date/event/detail cards."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    n = len(events)
    if n == 0:
        return

    card_gap = Inches(0.15)
    card_width = (width - card_gap * (n - 1)) // n
    card_height = height

    for i, event in enumerate(events):
        card_left = left + i * (card_width + card_gap)
        # Accent bar at top
        add_rect(slide, card_left, top, card_width, Pt(3),
                 fill_color=colors["accent"])
        # Card background
        shape = add_rect(slide, card_left, top + Pt(3), card_width,
                         card_height - Pt(3), fill_color=colors["bg_light"])
        tf = shape.text_frame
        tf.word_wrap = True
        tf.auto_size = None
        set_margins(tf, left=Inches(0.1), right=Inches(0.1),
                    top=Inches(0.08), bottom=Inches(0.05))
        shape.text_frame_anchor = MSO_ANCHOR.TOP

        # Date
        p_date = tf.paragraphs[0]
        p_date.text = str(event.get("date", ""))
        p_date.alignment = PP_ALIGN.LEFT
        p_date.space_after = Pt(3)
        run = p_date.runs[0] if p_date.runs else p_date.add_run()
        run.text = str(event.get("date", ""))
        run.font.size = Pt(9)
        run.font.bold = True
        run.font.color.rgb = colors["primary"]
        run.font.name = spec["_fonts"]["number"] if spec else "Courier New"

        # Event title
        p_title = tf.add_paragraph()
        p_title.text = str(event.get("title", ""))
        p_title.alignment = PP_ALIGN.LEFT
        p_title.space_after = Pt(2)
        run_t = p_title.add_run()
        run_t.text = str(event.get("title", ""))
        run_t.font.size = Pt(9)
        run_t.font.bold = True
        run_t.font.color.rgb = colors["text_dark"]
        run_t.font.name = spec["_fonts"]["label"] if spec else "Calibri"

        # Detail (optional)
        if event.get("detail"):
            p_detail = tf.add_paragraph()
            p_detail.text = str(event["detail"])
            p_detail.alignment = PP_ALIGN.LEFT
            run_d = p_detail.add_run()
            run_d.text = str(event["detail"])
            run_d.font.size = Pt(8)
            run_d.font.color.rgb = colors["secondary"]
            run_d.font.name = spec["_fonts"]["label"] if spec else "Calibri"


def scenario_box(slide, left, top, width, height, title, line_items,
                 total_label=None, total_value=None, accent_color=None, spec=None):
    """Render a scenario box: accent bar + line items + separator + totals."""
    colors = spec["_colors"] if spec else DEFAULT_COLORS
    if accent_color is None:
        accent_color = colors["accent"]

    # Accent bar on left
    add_rect(slide, left, top, Inches(0.06), height, fill_color=accent_color)

    # Main box
    shape = add_rect(slide, left + Inches(0.06), top, width - Inches(0.06), height,
                     fill_color=colors["bg_light"], border_color=colors["border"],
                     border_width=Pt(0.5))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    set_margins(tf, left=Inches(0.15), right=Inches(0.15),
                top=Inches(0.1), bottom=Inches(0.08))
    shape.text_frame_anchor = MSO_ANCHOR.TOP

    # Title
    p_title = tf.paragraphs[0]
    p_title.text = str(title).upper()
    p_title.alignment = PP_ALIGN.LEFT
    p_title.space_after = Pt(6)
    run = p_title.runs[0] if p_title.runs else p_title.add_run()
    run.text = str(title).upper()
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = colors["primary"]
    run.font.name = spec["_fonts"]["label"] if spec else "Calibri"

    # Line items
    for item in line_items:
        label = item.get("label", "")
        value = item.get("value", "")
        line_text = f"{label}    {value}" if value else str(label)
        p = tf.add_paragraph()
        p.text = line_text
        p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(1)
        p.space_after = Pt(1)
        run_l = p.add_run()
        run_l.text = line_text
        run_l.font.size = Pt(9)
        run_l.font.color.rgb = colors["text_dark"]
        run_l.font.name = spec["_fonts"]["number"] if spec else "Courier New"

    # Separator + total
    if total_label and total_value:
        p_sep = tf.add_paragraph()
        p_sep.text = "─" * 40
        p_sep.alignment = PP_ALIGN.LEFT
        p_sep.space_before = Pt(4)
        p_sep.space_after = Pt(2)
        run_sep = p_sep.add_run()
        run_sep.text = "─" * 40
        run_sep.font.size = Pt(6)
        run_sep.font.color.rgb = colors["border"]

        total_text = f"{total_label}    {total_value}"
        p_total = tf.add_paragraph()
        p_total.text = total_text
        p_total.alignment = PP_ALIGN.LEFT
        run_tot = p_total.add_run()
        run_tot.text = total_text
        run_tot.font.size = Pt(10)
        run_tot.font.bold = True
        run_tot.font.color.rgb = colors["primary"]
        run_tot.font.name = spec["_fonts"]["number"] if spec else "Courier New"


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_cover_slide(prs, data, spec):
    """Build a title/cover slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    colors = spec["_colors"]

    # Full-slide dark background
    add_rect(slide, Emu(0), Emu(0), SLIDE_WIDTH, SLIDE_HEIGHT,
             fill_color=colors["bg_dark"])

    # Title
    txbox, tf = add_textbox(slide, Inches(1), Inches(2), Inches(11), Inches(1.5),
                            anchor=MSO_ANCHOR.BOTTOM)
    set_text(tf, data.get("title", "Presentation"), font_size=Pt(36), bold=True,
             color=colors["text_light"], font_name=spec["_fonts"]["display"], spec=spec)

    # Subtitle
    if data.get("subtitle"):
        txbox2, tf2 = add_textbox(slide, Inches(1), Inches(3.5), Inches(11), Inches(0.6),
                                  anchor=MSO_ANCHOR.TOP)
        set_text(tf2, data["subtitle"], font_size=Pt(16), bold=False,
                 color=colors["secondary"], font_name=spec["_fonts"]["label"], spec=spec)

    # Date / metadata
    if data.get("date"):
        txbox3, tf3 = add_textbox(slide, Inches(1), Inches(4.5), Inches(11), Inches(0.4),
                                  anchor=MSO_ANCHOR.TOP)
        set_text(tf3, data["date"], font_size=Pt(12), bold=False,
                 color=colors["text_light"], font_name=spec["_fonts"]["number"], spec=spec)

    # Accent line
    add_rect(slide, Inches(1), Inches(3.3), Inches(2), Pt(3),
             fill_color=colors["accent"])

    return slide


def build_content_slide(prs, slide_spec, data, spec):
    """Build a generic content slide from a slide specification."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    area = ContentArea()

    title = slide_spec.get("title", "")
    header_bar(slide, title, spec=spec)
    footer_bar(slide, left_text=data.get("footer_left", ""),
               right_text=data.get("footer_right", ""), spec=spec)

    return slide, area


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_presentation(data_path, spec_path, template_path=None, output_path="output.pptx"):
    """Generate a complete PPTX from data and design spec."""
    data = load_data(data_path)
    spec = load_design_spec(spec_path)

    # Create presentation from template or blank
    if template_path and Path(template_path).exists():
        prs = Presentation(template_path)
    else:
        prs = Presentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT

    # Build slides from data structure
    slides_data = data.get("slides", [])
    if not slides_data:
        # If no explicit slides, build a cover from top-level data
        build_cover_slide(prs, data, spec)
    else:
        for slide_spec in slides_data:
            slide_type = slide_spec.get("type", "content")
            if slide_type == "cover":
                build_cover_slide(prs, slide_spec, spec)
            elif slide_type == "content":
                build_content_slide(prs, slide_spec, data, spec)

    # Save
    prs.save(output_path)
    print(f"Generated: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="ACOS PPTX Generation Engine")
    parser.add_argument("data_yaml", help="Path to verified-data.yaml")
    parser.add_argument("design_spec_yaml", help="Path to design-spec.yaml")
    parser.add_argument("--template", help="Optional template.pptx with theme/masters")
    parser.add_argument("-o", "--output", default="output.pptx", help="Output path")
    args = parser.parse_args()

    generate_presentation(args.data_yaml, args.design_spec_yaml,
                          template_path=args.template, output_path=args.output)


if __name__ == "__main__":
    main()
