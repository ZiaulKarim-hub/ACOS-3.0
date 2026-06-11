#!/usr/bin/env python3
"""
ACOS Loan Document Generator — SVG Chart Generation Utility

Generates SVG charts embeddable in both HTML→PDF and DOCX pipelines.
No external dependencies — pure Python 3 stdlib SVG generation.

Usage:
  python3 generate-chart.py --type bar --data '{"labels":["LTV","DSCR"],"values":[65.6,1.7]}' --output chart.svg
  python3 generate-chart.py --type gauge --data '{"value":1.7,"min":0,"max":3,"label":"DSCR","thresholds":[1.0,1.25]}' --output dscr.svg
  python3 generate-chart.py --type waterfall --data '{"items":[{"label":"Property Value","value":3200000},{"label":"Senior Debt","value":-2100000}]}' --output ltv.svg
  python3 generate-chart.py --type matrix --data '{"score":7.5,"label":"Credit Score","categories":[{"name":"Finance","min":8,"color":"#28a745"},{"name":"Conditional","min":6,"color":"#ffc107"},{"name":"Decline","min":0,"color":"#dc3545"}]}' --output matrix.svg

Supported chart types:
  bar       — Horizontal or vertical bar chart
  waterfall — Waterfall chart (additive/subtractive)
  gauge     — Semicircular gauge with thresholds
  donut     — Donut/pie chart
  matrix    — Color-coded recommendation matrix cell
  radar     — Spider/radar chart (4-pillar scores)
  rag_table — Red-Amber-Green metrics table
  line      — Line/trend chart
  stacked   — Stacked horizontal bar
  heatmap   — Color-coded grid (sensitivity analysis)
  area      — Filled area chart (amortization, cash flow)
"""

import sys
import json
import math
import argparse
from pathlib import Path


# ── Color Palette (institutional finance) ───────────────────────────────────

COLORS = {
    "primary": "#003366",
    "secondary": "#0066cc",
    "accent": "#4d94db",
    "light": "#b3d1f0",
    "bg": "#f8f9fa",
    "text": "#1a1a1a",
    "grid": "#e0e0e0",
    "green": "#28a745",
    "amber": "#ffc107",
    "red": "#dc3545",
    "green_light": "#d4edda",
    "amber_light": "#fff3cd",
    "red_light": "#f8d7da",
}

CHART_PALETTE = ["#003366", "#0066cc", "#4d94db", "#b3d1f0", "#006644", "#cc6600", "#993366", "#666666"]


def escape_xml(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def format_currency(value):
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"${value/1_000:,.0f}K"
    return f"${value:,.0f}"


def format_number(value, fmt="auto"):
    if fmt == "currency":
        return format_currency(value)
    if fmt == "percent":
        return f"{value:.1f}%"
    if fmt == "ratio":
        return f"{value:.2f}x"
    if isinstance(value, float):
        return f"{value:,.1f}" if value != int(value) else f"{int(value):,}"
    return f"{value:,}"


# ── Bar Chart ───────────────────────────────────────────────────────────────

def generate_bar_chart(data, width=500, height=300):
    labels = data.get("labels", [])
    values = data.get("values", [])
    fmt = data.get("format", "auto")
    title = data.get("title", "")
    horizontal = data.get("horizontal", True)
    colors = data.get("colors", CHART_PALETTE)

    n = len(labels)
    if n == 0:
        return "<svg></svg>"

    margin = {"top": 40, "right": 20, "bottom": 40, "left": 120 if horizontal else 60}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]
    max_val = max(abs(v) for v in values) * 1.15

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" '
                   f'font-size="12" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    if horizontal:
        bar_h = min(plot_h / n * 0.7, 30)
        gap = plot_h / n
        for i, (label, value) in enumerate(zip(labels, values)):
            y = margin["top"] + i * gap + (gap - bar_h) / 2
            bar_w = (abs(value) / max_val) * plot_w if max_val > 0 else 0
            color = colors[i % len(colors)]
            svg.append(f'<rect x="{margin["left"]}" y="{y}" width="{bar_w}" height="{bar_h}" '
                       f'fill="{color}" rx="2"/>')
            svg.append(f'<text x="{margin["left"] - 8}" y="{y + bar_h/2 + 4}" '
                       f'text-anchor="end" font-size="9" fill="{COLORS["text"]}">{escape_xml(label)}</text>')
            svg.append(f'<text x="{margin["left"] + bar_w + 5}" y="{y + bar_h/2 + 4}" '
                       f'font-size="9" fill="{COLORS["text"]}">{format_number(value, fmt)}</text>')
    else:
        bar_w = min(plot_w / n * 0.7, 50)
        gap = plot_w / n
        for i, (label, value) in enumerate(zip(labels, values)):
            x = margin["left"] + i * gap + (gap - bar_w) / 2
            bar_h_val = (abs(value) / max_val) * plot_h if max_val > 0 else 0
            y = margin["top"] + plot_h - bar_h_val
            color = colors[i % len(colors)]
            svg.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h_val}" '
                       f'fill="{color}" rx="2"/>')
            svg.append(f'<text x="{x + bar_w/2}" y="{margin["top"] + plot_h + 15}" '
                       f'text-anchor="middle" font-size="8" fill="{COLORS["text"]}">{escape_xml(label)}</text>')
            svg.append(f'<text x="{x + bar_w/2}" y="{y - 5}" text-anchor="middle" '
                       f'font-size="8" fill="{COLORS["text"]}">{format_number(value, fmt)}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Gauge Chart ─────────────────────────────────────────────────────────────

def generate_gauge_chart(data, width=250, height=160):
    value = data.get("value", 0)
    min_val = data.get("min", 0)
    max_val = data.get("max", 3)
    label = data.get("label", "")
    thresholds = data.get("thresholds", [])
    fmt = data.get("format", "ratio")

    cx, cy = width / 2, height - 20
    radius = min(width / 2 - 20, height - 40)
    stroke_w = 18

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    # Background arc
    svg.append(f'<path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}" '
               f'fill="none" stroke="{COLORS["grid"]}" stroke-width="{stroke_w}" stroke-linecap="round"/>')

    # Threshold color segments
    if thresholds:
        sorted_t = sorted(thresholds)
        segments = []
        prev = min_val
        segment_colors = [COLORS["red"], COLORS["amber"], COLORS["green"]]
        for i, t in enumerate(sorted_t):
            segments.append((prev, t, segment_colors[i] if i < len(segment_colors) else COLORS["green"]))
            prev = t
        # Final (best) segment always uses the highest "good" color so a
        # single-threshold pass/fail gauge reads red->green, not red->amber.
        segments.append((prev, max_val, segment_colors[-1]))

        for start, end, color in segments:
            start_angle = math.pi * (1 - (start - min_val) / (max_val - min_val))
            end_angle = math.pi * (1 - (end - min_val) / (max_val - min_val))
            x1 = cx + radius * math.cos(start_angle)
            y1 = cy - radius * math.sin(start_angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy - radius * math.sin(end_angle)
            large_arc = 1 if (start_angle - end_angle) > math.pi else 0
            svg.append(f'<path d="M {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2}" '
                       f'fill="none" stroke="{color}" stroke-width="{stroke_w}" stroke-linecap="butt" opacity="0.3"/>')

    # Value needle
    clamped = max(min_val, min(value, max_val))
    angle = math.pi * (1 - (clamped - min_val) / (max_val - min_val))
    needle_len = radius - 10
    nx = cx + needle_len * math.cos(angle)
    ny = cy - needle_len * math.sin(angle)
    svg.append(f'<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" '
               f'stroke="{COLORS["primary"]}" stroke-width="3" stroke-linecap="round"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{COLORS["primary"]}"/>')

    # Value text
    svg.append(f'<text x="{cx}" y="{cy - 15}" text-anchor="middle" '
               f'font-size="18" font-weight="700" fill="{COLORS["primary"]}">{format_number(value, fmt)}</text>')
    if label:
        svg.append(f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" '
                   f'font-size="10" fill="{COLORS["text"]}">{escape_xml(label)}</text>')

    # Min/max labels
    svg.append(f'<text x="{cx - radius}" y="{cy + 15}" text-anchor="middle" '
               f'font-size="8" fill="#999">{format_number(min_val, fmt)}</text>')
    svg.append(f'<text x="{cx + radius}" y="{cy + 15}" text-anchor="middle" '
               f'font-size="8" fill="#999">{format_number(max_val, fmt)}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Recommendation Matrix Cell ──────────────────────────────────────────────

def generate_matrix_chart(data, width=300, height=80):
    score = data.get("score", 0)
    label = data.get("label", "Credit Score")
    categories = data.get("categories", [
        {"name": "Finance", "min": 8, "color": COLORS["green"], "bg": COLORS["green_light"]},
        {"name": "Conditional", "min": 6, "color": COLORS["amber"], "bg": COLORS["amber_light"]},
        {"name": "Decline", "min": 0, "color": COLORS["red"], "bg": COLORS["red_light"]},
    ])

    # Find which category the score falls into. Sort descending by min so the
    # highest matching band wins regardless of the input order of categories.
    active_cat = categories[-1]  # default to worst
    for cat in sorted(categories, key=lambda c: c["min"], reverse=True):
        if score >= cat["min"]:
            active_cat = cat
            break

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    # Background
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" '
               f'fill="{active_cat.get("bg", "#f0f0f0")}" rx="4"/>')
    svg.append(f'<rect x="0" y="0" width="{width}" height="{height}" '
               f'fill="none" stroke="{active_cat["color"]}" stroke-width="2" rx="4"/>')

    # Score
    svg.append(f'<text x="20" y="{height/2 + 6}" font-size="24" font-weight="700" '
               f'fill="{active_cat["color"]}">{score:.1f}</text>')

    # Label and recommendation
    svg.append(f'<text x="80" y="{height/2 - 5}" font-size="10" '
               f'fill="{COLORS["text"]}">{escape_xml(label)}</text>')
    svg.append(f'<text x="80" y="{height/2 + 12}" font-size="14" font-weight="600" '
               f'fill="{active_cat["color"]}">{escape_xml(active_cat["name"])}</text>')

    # Scale indicator
    scale_x = 180
    scale_w = width - scale_x - 15
    for cat in reversed(categories):
        cat_w = scale_w * (1 / len(categories))
        svg.append(f'<rect x="{scale_x}" y="{height/2 - 6}" width="{cat_w}" height="12" '
                   f'fill="{cat["color"]}" opacity="0.3"/>')
        scale_x += cat_w

    # Score marker on scale
    score_pct = min(1, max(0, score / 10))
    marker_x = 180 + score_pct * (width - 195)
    svg.append(f'<circle cx="{marker_x}" cy="{height/2}" r="4" fill="{active_cat["color"]}"/>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Waterfall Chart ─────────────────────────────────────────────────────────

def generate_waterfall_chart(data, width=500, height=300):
    items = data.get("items", [])
    title = data.get("title", "")
    fmt = data.get("format", "currency")

    if not items:
        return "<svg></svg>"

    margin = {"top": 40, "right": 30, "bottom": 50, "left": 80}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    # Calculate running totals
    running = 0
    bars = []
    for item in items:
        start = running
        value = item["value"]
        running += value
        bars.append({"label": item["label"], "start": start, "end": running, "value": value})

    all_vals = [b["start"] for b in bars] + [b["end"] for b in bars]
    min_val = min(0, min(all_vals))
    max_val = max(all_vals) * 1.1

    def scale_y(v):
        return margin["top"] + plot_h * (1 - (v - min_val) / (max_val - min_val))

    n = len(bars)
    bar_w = min(plot_w / n * 0.6, 60)
    gap = plot_w / n

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="20" text-anchor="middle" '
                   f'font-size="12" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    # Zero line
    zero_y = scale_y(0)
    svg.append(f'<line x1="{margin["left"]}" y1="{zero_y}" x2="{width - margin["right"]}" y2="{zero_y}" '
               f'stroke="{COLORS["grid"]}" stroke-width="1"/>')

    for i, bar in enumerate(bars):
        x = margin["left"] + i * gap + (gap - bar_w) / 2
        y_top = scale_y(max(bar["start"], bar["end"]))
        y_bot = scale_y(min(bar["start"], bar["end"]))
        h = y_bot - y_top
        color = COLORS["green"] if bar["value"] >= 0 else COLORS["red"]

        svg.append(f'<rect x="{x}" y="{y_top}" width="{bar_w}" height="{h}" fill="{color}" rx="1"/>')

        # Connector line to next bar
        if i < n - 1:
            next_x = margin["left"] + (i + 1) * gap + (gap - bar_w) / 2
            conn_y = scale_y(bar["end"])
            svg.append(f'<line x1="{x + bar_w}" y1="{conn_y}" x2="{next_x}" y2="{conn_y}" '
                       f'stroke="{COLORS["grid"]}" stroke-width="1" stroke-dasharray="3,3"/>')

        # Value label
        svg.append(f'<text x="{x + bar_w/2}" y="{y_top - 5}" text-anchor="middle" '
                   f'font-size="8" fill="{COLORS["text"]}">{format_number(bar["value"], fmt)}</text>')

        # X-axis label
        svg.append(f'<text x="{x + bar_w/2}" y="{margin["top"] + plot_h + 15}" '
                   f'text-anchor="middle" font-size="7" fill="{COLORS["text"]}">{escape_xml(bar["label"])}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Donut Chart ─────────────────────────────────────────────────────────────

def generate_donut_chart(data, width=250, height=250):
    segments = data.get("segments", [])
    title = data.get("title", "")
    center_label = data.get("center_label", "")
    center_value = data.get("center_value", "")

    if not segments:
        return "<svg></svg>"

    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 30
    inner_radius = radius * 0.55
    total = sum(s["value"] for s in segments)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{cx}" y="15" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    angle = -math.pi / 2  # start at top
    for i, seg in enumerate(segments):
        pct = seg["value"] / total if total > 0 else 0
        sweep = 2 * math.pi * pct
        color = seg.get("color", CHART_PALETTE[i % len(CHART_PALETTE)])

        x1_outer = cx + radius * math.cos(angle)
        y1_outer = cy + radius * math.sin(angle)
        x2_outer = cx + radius * math.cos(angle + sweep)
        y2_outer = cy + radius * math.sin(angle + sweep)
        x1_inner = cx + inner_radius * math.cos(angle + sweep)
        y1_inner = cy + inner_radius * math.sin(angle + sweep)
        x2_inner = cx + inner_radius * math.cos(angle)
        y2_inner = cy + inner_radius * math.sin(angle)

        large_arc = 1 if sweep > math.pi else 0

        path = (f"M {x1_outer} {y1_outer} "
                f"A {radius} {radius} 0 {large_arc} 1 {x2_outer} {y2_outer} "
                f"L {x1_inner} {y1_inner} "
                f"A {inner_radius} {inner_radius} 0 {large_arc} 0 {x2_inner} {y2_inner} Z")

        svg.append(f'<path d="{path}" fill="{color}"/>')
        angle += sweep

    # Center text
    if center_value:
        svg.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" '
                   f'font-size="18" font-weight="700" fill="{COLORS["primary"]}">{escape_xml(center_value)}</text>')
    if center_label:
        svg.append(f'<text x="{cx}" y="{cy + 14}" text-anchor="middle" '
                   f'font-size="9" fill="{COLORS["text"]}">{escape_xml(center_label)}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Radar / Spider Chart ─────────────────────────────────────────────────────

def generate_radar_chart(data, width=300, height=300):
    segments = data.get("segments", [])
    title = data.get("title", "")

    if not segments:
        return "<svg></svg>"

    n = len(segments)
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 40
    angle_step = 2 * math.pi / n

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{cx}" y="15" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    # Grid rings
    for ring in [0.25, 0.5, 0.75, 1.0]:
        r = radius * ring
        points = []
        for i in range(n):
            angle = -math.pi / 2 + i * angle_step
            points.append(f"{cx + r * math.cos(angle)},{cy + r * math.sin(angle)}")
        svg.append(f'<polygon points="{" ".join(points)}" fill="none" '
                   f'stroke="{COLORS["grid"]}" stroke-width="0.5"/>')

    # Axis lines
    for i in range(n):
        angle = -math.pi / 2 + i * angle_step
        x2 = cx + radius * math.cos(angle)
        y2 = cy + radius * math.sin(angle)
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x2}" y2="{y2}" '
                   f'stroke="{COLORS["grid"]}" stroke-width="0.5"/>')

    # Data polygon
    max_val = data.get("max_value", 10)
    points = []
    for i, seg in enumerate(segments):
        val = seg.get("value", 0)
        r = radius * (val / max_val)
        angle = -math.pi / 2 + i * angle_step
        points.append(f"{cx + r * math.cos(angle)},{cy + r * math.sin(angle)}")

    svg.append(f'<polygon points="{" ".join(points)}" fill="{COLORS["primary"]}" '
               f'fill-opacity="0.2" stroke="{COLORS["primary"]}" stroke-width="2"/>')

    # Data points and labels
    for i, seg in enumerate(segments):
        val = seg.get("value", 0)
        label = seg.get("label", "")
        r_pt = radius * (val / max_val)
        r_label = radius + 15
        angle = -math.pi / 2 + i * angle_step
        px = cx + r_pt * math.cos(angle)
        py = cy + r_pt * math.sin(angle)
        lx = cx + r_label * math.cos(angle)
        ly = cy + r_label * math.sin(angle)
        svg.append(f'<circle cx="{px}" cy="{py}" r="3" fill="{COLORS["primary"]}"/>')
        anchor = "middle"
        if math.cos(angle) > 0.3:
            anchor = "start"
        elif math.cos(angle) < -0.3:
            anchor = "end"
        svg.append(f'<text x="{lx}" y="{ly + 3}" text-anchor="{anchor}" '
                   f'font-size="8" fill="{COLORS["text"]}">{escape_xml(label)}</text>')
        svg.append(f'<text x="{px}" y="{py - 6}" text-anchor="middle" '
                   f'font-size="7" fill="{COLORS["primary"]}">{val:.1f}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── RAG Table (Red-Amber-Green metrics table) ───────────────────────────────

def generate_rag_table_chart(data, width=500, height=None):
    rows = data.get("rows", [])
    title = data.get("title", "Key Metrics")

    if not rows:
        return "<svg></svg>"

    row_h = 28
    header_h = 32
    padding = 10
    height = height or (header_h + len(rows) * row_h + padding * 2 + 20)

    rag_colors = {"green": "#22C55E", "amber": "#EAB308", "red": "#EF4444", "gray": "#999"}
    rag_bg = {"green": "#F0FDF4", "amber": "#FEFCE8", "red": "#FEF2F2", "gray": "#F5F5F5"}

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="16" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    y_start = 24
    col_widths = [0.30, 0.20, 0.20, 0.15, 0.15]
    headers = ["Metric", "Value", "Threshold", "Status", ""]

    # Header row
    x = 0
    for i, (header, cw) in enumerate(zip(headers, col_widths)):
        w = width * cw
        svg.append(f'<rect x="{x}" y="{y_start}" width="{w}" height="{header_h}" fill="{COLORS["primary"]}"/>')
        svg.append(f'<text x="{x + 8}" y="{y_start + 20}" font-size="9" font-weight="600" fill="white">{header}</text>')
        x += w

    # Data rows
    for ri, row in enumerate(rows):
        y = y_start + header_h + ri * row_h
        color = row.get("color", "gray")
        bg = rag_bg.get(color, "#fff")
        fg = rag_colors.get(color, "#999")

        # Alternating background
        row_bg = bg if ri % 2 == 0 else "#fff"
        svg.append(f'<rect x="0" y="{y}" width="{width}" height="{row_h}" fill="{row_bg}"/>')
        svg.append(f'<line x1="0" y1="{y + row_h}" x2="{width}" y2="{y + row_h}" stroke="#eee" stroke-width="0.5"/>')

        x = 0
        vals = [row.get("metric", ""), row.get("value", ""), row.get("threshold", ""), ""]
        for i, (val, cw) in enumerate(zip(vals, col_widths)):
            w = width * cw
            svg.append(f'<text x="{x + 8}" y="{y + 18}" font-size="8.5" fill="{COLORS["text"]}">{escape_xml(str(val))}</text>')
            x += w

        # Status dot
        dot_x = x - width * col_widths[-1] + 20
        svg.append(f'<circle cx="{dot_x}" cy="{y + 14}" r="5" fill="{fg}"/>')
        svg.append(f'<text x="{dot_x + 10}" y="{y + 18}" font-size="8" font-weight="600" fill="{fg}">'
                   f'{color.upper()}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Line / Trend Chart ──────────────────────────────────────────────────────

def generate_line_chart(data, width=500, height=250):
    points = data.get("points", [])
    title = data.get("title", "")
    fmt = data.get("format", "auto")
    x_labels = data.get("x_labels", [])

    if not points:
        return "<svg></svg>"

    margin = {"top": 35, "right": 20, "bottom": 40, "left": 60}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    min_val = min(points) * 0.9
    max_val = max(points) * 1.1
    val_range = max_val - min_val if max_val != min_val else 1

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="18" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    # Grid lines
    for i in range(5):
        y = margin["top"] + plot_h * i / 4
        val = max_val - val_range * i / 4
        svg.append(f'<line x1="{margin["left"]}" y1="{y}" x2="{width - margin["right"]}" y2="{y}" '
                   f'stroke="{COLORS["grid"]}" stroke-width="0.5"/>')
        svg.append(f'<text x="{margin["left"] - 5}" y="{y + 3}" text-anchor="end" '
                   f'font-size="7" fill="#999">{format_number(val, fmt)}</text>')

    # Line path
    n = len(points)
    path_parts = []
    for i, val in enumerate(points):
        x = margin["left"] + (i / max(n - 1, 1)) * plot_w
        y = margin["top"] + plot_h * (1 - (val - min_val) / val_range)
        path_parts.append(f"{'M' if i == 0 else 'L'} {x} {y}")

    svg.append(f'<path d="{" ".join(path_parts)}" fill="none" '
               f'stroke="{COLORS["primary"]}" stroke-width="2"/>')

    # Data points
    for i, val in enumerate(points):
        x = margin["left"] + (i / max(n - 1, 1)) * plot_w
        y = margin["top"] + plot_h * (1 - (val - min_val) / val_range)
        svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{COLORS["primary"]}"/>')
        if x_labels and i < len(x_labels):
            svg.append(f'<text x="{x}" y="{margin["top"] + plot_h + 15}" text-anchor="middle" '
                       f'font-size="7" fill="{COLORS["text"]}">{escape_xml(str(x_labels[i]))}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Stacked Bar Chart ───────────────────────────────────────────────────────

def generate_stacked_chart(data, width=500, height=80):
    segments = data.get("segments", [])
    title = data.get("title", "")
    fmt = data.get("format", "currency")

    if not segments:
        return "<svg></svg>"

    total = sum(s["value"] for s in segments)
    bar_y = 35 if title else 10
    bar_h = 30
    label_y = bar_y + bar_h + 14

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {bar_y + bar_h + 30}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="16" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    x = 0
    for i, seg in enumerate(segments):
        w = (seg["value"] / total) * width if total > 0 else 0
        color = seg.get("color", CHART_PALETTE[i % len(CHART_PALETTE)])
        svg.append(f'<rect x="{x}" y="{bar_y}" width="{w}" height="{bar_h}" fill="{color}"/>')
        if w > 40:
            svg.append(f'<text x="{x + w/2}" y="{bar_y + bar_h/2 + 4}" text-anchor="middle" '
                       f'font-size="8" font-weight="600" fill="white">{format_number(seg["value"], fmt)}</text>')
        svg.append(f'<text x="{x + w/2}" y="{label_y}" text-anchor="middle" '
                   f'font-size="7" fill="{COLORS["text"]}">{escape_xml(seg.get("label", ""))}</text>')
        x += w

    svg.append('</svg>')
    return "\n".join(svg)


# ── Heatmap Chart ───────────────────────────────────────────────────────────

def generate_heatmap_chart(data, width=400, height=None):
    rows = data.get("rows", [])
    cols = data.get("cols", [])
    values = data.get("values", [])
    title = data.get("title", "")

    if not rows or not cols or not values:
        return "<svg></svg>"

    cell_w = min(60, (width - 80) / len(cols))
    cell_h = 28
    margin_left = 80
    margin_top = 50 if title else 30
    height = height or (margin_top + len(rows) * cell_h + 20)

    flat_vals = [v for row in values for v in row if v is not None]
    min_v = min(flat_vals) if flat_vals else 0
    max_v = max(flat_vals) if flat_vals else 1

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="18" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    # Column headers
    for ci, col in enumerate(cols):
        x = margin_left + ci * cell_w + cell_w / 2
        svg.append(f'<text x="{x}" y="{margin_top - 5}" text-anchor="middle" '
                   f'font-size="7" font-weight="600" fill="{COLORS["text"]}">{escape_xml(str(col))}</text>')

    # Cells
    for ri, row_label in enumerate(rows):
        y = margin_top + ri * cell_h
        svg.append(f'<text x="{margin_left - 5}" y="{y + cell_h/2 + 3}" text-anchor="end" '
                   f'font-size="7" fill="{COLORS["text"]}">{escape_xml(str(row_label))}</text>')

        for ci in range(len(cols)):
            val = values[ri][ci] if ri < len(values) and ci < len(values[ri]) else None
            x = margin_left + ci * cell_w
            if val is not None:
                t = (val - min_v) / (max_v - min_v) if max_v != min_v else 0.5
                # Green (good) to Red (bad)
                r = int(239 * (1 - t) + 34 * t)
                g = int(68 * (1 - t) + 197 * t)
                b = int(68 * (1 - t) + 94 * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
                svg.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" '
                           f'fill="{color}" opacity="0.7" stroke="white" stroke-width="1"/>')
                svg.append(f'<text x="{x + cell_w/2}" y="{y + cell_h/2 + 3}" text-anchor="middle" '
                           f'font-size="8" fill="white" font-weight="600">{val:.2f}x</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Area Chart ──────────────────────────────────────────────────────────────

def generate_area_chart(data, width=500, height=250):
    """Area chart — delegates to line chart with fill."""
    points = data.get("points", [])
    title = data.get("title", "")
    fmt = data.get("format", "auto")
    x_labels = data.get("x_labels", [])

    if not points:
        return "<svg></svg>"

    margin = {"top": 35, "right": 20, "bottom": 40, "left": 60}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    min_val = 0
    max_val = max(points) * 1.1
    val_range = max_val - min_val if max_val != min_val else 1

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'font-family="Calibri, Helvetica, Arial, sans-serif">']

    if title:
        svg.append(f'<text x="{width/2}" y="18" text-anchor="middle" '
                   f'font-size="11" font-weight="600" fill="{COLORS["primary"]}">{escape_xml(title)}</text>')

    n = len(points)
    baseline_y = margin["top"] + plot_h

    # Fill area
    area_parts = [f"M {margin['left']} {baseline_y}"]
    for i, val in enumerate(points):
        x = margin["left"] + (i / max(n - 1, 1)) * plot_w
        y = margin["top"] + plot_h * (1 - (val - min_val) / val_range)
        area_parts.append(f"L {x} {y}")
    area_parts.append(f"L {margin['left'] + plot_w} {baseline_y} Z")

    svg.append(f'<path d="{" ".join(area_parts)}" fill="{COLORS["primary"]}" fill-opacity="0.15"/>')

    # Line on top
    line_parts = []
    for i, val in enumerate(points):
        x = margin["left"] + (i / max(n - 1, 1)) * plot_w
        y = margin["top"] + plot_h * (1 - (val - min_val) / val_range)
        line_parts.append(f"{'M' if i == 0 else 'L'} {x} {y}")

    svg.append(f'<path d="{" ".join(line_parts)}" fill="none" '
               f'stroke="{COLORS["primary"]}" stroke-width="2"/>')

    # X labels
    for i in range(n):
        x = margin["left"] + (i / max(n - 1, 1)) * plot_w
        if x_labels and i < len(x_labels):
            svg.append(f'<text x="{x}" y="{baseline_y + 15}" text-anchor="middle" '
                       f'font-size="7" fill="{COLORS["text"]}">{escape_xml(str(x_labels[i]))}</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ── Main ────────────────────────────────────────────────────────────────────

CHART_GENERATORS = {
    "bar": generate_bar_chart,
    "gauge": generate_gauge_chart,
    "matrix": generate_matrix_chart,
    "waterfall": generate_waterfall_chart,
    "donut": generate_donut_chart,
    "radar": generate_radar_chart,
    "rag_table": generate_rag_table_chart,
    "line": generate_line_chart,
    "stacked": generate_stacked_chart,
    "heatmap": generate_heatmap_chart,
    "area": generate_area_chart,
}


def main():
    parser = argparse.ArgumentParser(description="Generate SVG charts for loan documents")
    parser.add_argument("--type", "-t", required=True, choices=CHART_GENERATORS.keys(),
                        help="Chart type")
    parser.add_argument("--data", "-d",
                        help="JSON data for the chart (inline string)")
    parser.add_argument("--data-file",
                        help="Path to JSON data file (alternative to --data)")
    parser.add_argument("--output", "-o", help="Output SVG file (default: stdout)")
    parser.add_argument("--width", type=int, default=None, help="Chart width in px")
    parser.add_argument("--height", type=int, default=None, help="Chart height in px")
    args = parser.parse_args()

    if args.data_file:
        try:
            with open(args.data_file) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"ERROR: Failed to read data file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON data: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: either --data or --data-file is required", file=sys.stderr)
        sys.exit(1)

    kwargs = {}
    if args.width:
        kwargs["width"] = args.width
    if args.height:
        kwargs["height"] = args.height

    svg = CHART_GENERATORS[args.type](data, **kwargs)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(svg)
        print(f"Chart generated: {args.output}", file=sys.stderr)
    else:
        print(svg)


if __name__ == "__main__":
    main()
