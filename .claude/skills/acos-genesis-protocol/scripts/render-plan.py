#!/usr/bin/env python3
"""
render-plan.py — render a complete, self-contained Plan HTML for acos-genesis-protocol.

Companion to render-library.py. Where library.html is the *browsable component
catalog*, plan.html is the *narrative plan a human reads top-to-bottom*: vision,
coverage, success-criteria map, an auto-laid-out DATA-FLOW DIAGRAM (inline SVG)
with a "how to read it" guide, the build phases, the full wiring table, and a
per-component reference.

Inputs (all under planning/preeng-unix/<feature-id>/):
  component-tree.json     (REQUIRED) — nodes, contracts, verifiers, reuse
  integration-map.json    (optional) — child->parent wiring + data notes
  build-plan.json         (optional) — leaves-first order + levels + repair
  success-criteria.json   (optional) — SC list with measures + covered_by
  coverage_qa_report.json (optional) — coverage gate verdict
  vision.md               (optional) — product vision prose

Pure Python 3 stdlib — NO external packages, NO API calls, NO network. The SVG
is computed and emitted directly (no Mermaid/Graphviz/headless browser), so the
output renders fully OFFLINE with system fonts only.

Usage:
  render-plan.py <feature-dir> [--out <path>]

Exit 0 = rendered. 1 = usage/missing input. 2 = malformed JSON.
"""
import json
import os
import re
import sys
import math
from datetime import datetime, timezone

# ----------------------------------------------------------------------------- utils

def die(msg, code):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def load_json(path, required=True):
    if not os.path.isfile(path):
        if required:
            die("MISSING: %s" % path, 1)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        die("MALFORMED JSON in %s: %s" % (path, e), 2)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wrap_text(s, max_chars, max_lines):
    """Greedy word-wrap into <=max_lines lines of <=max_chars chars."""
    words = str(s).split()
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
        if len(lines) == max_lines:
            break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and (len(" ".join(words)) > len(" ".join(lines))):
        lines[-1] = lines[-1][:max_chars - 1].rstrip() + "…"
    return lines or [""]


def md_lite(text):
    """Very small markdown -> HTML for the vision blurb (headings/bold/lists/paras)."""
    out, in_ul = [], False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if in_ul:
                out.append("</ul>"); in_ul = False
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            if in_ul:
                out.append("</ul>"); in_ul = False
            lvl = min(len(h.group(1)) + 2, 6)
            out.append("<h%d>%s</h%d>" % (lvl, inline_md(h.group(2)), lvl))
            continue
        b = re.match(r"^\s*[-*]\s+(.*)$", line)
        if b:
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append("<li>%s</li>" % inline_md(b.group(1)))
            continue
        if in_ul:
            out.append("</ul>"); in_ul = False
        out.append("<p>%s</p>" % inline_md(line))
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def inline_md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


# ----------------------------------------------------------------------------- model

def classify(node):
    children = node.get("children") or []
    shared = bool((node.get("reuse") or {}).get("known_consumers"))
    blob = (str(node.get("name", "")) + " " + str(node.get("purpose", ""))).lower()
    gate = ("hard gate" in blob) or ("choke point" in blob) or ("gate)" in blob)
    if node.get("depth") == 0:
        kind = "root"
    elif children:
        kind = "module"
    else:
        kind = "leaf"
    return kind, shared, gate


def module_of(nid, by_id):
    n = by_id.get(nid)
    if n is None:
        return None
    d = n.get("depth", 0)
    if d <= 1:
        return nid
    p = n.get("parent")
    while p is not None and by_id.get(p, {}).get("depth", 0) > 1:
        p = by_id[p].get("parent")
    return p


def topo_order(items, edges):
    """Kahn topological sort; stable fallback to input order on ties/cycles."""
    items = list(items)
    indeg = {i: 0 for i in items}
    adj = {i: [] for i in items}
    for a, b in edges:
        if a in indeg and b in indeg and a != b:
            adj[a].append(b); indeg[b] += 1
    ready = [i for i in items if indeg[i] == 0]
    order, seen = [], set()
    while ready:
        ready.sort(key=lambda x: items.index(x))
        n = ready.pop(0)
        if n in seen:
            continue
        seen.add(n); order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    for i in items:           # append any cycle remnants in stable order
        if i not in seen:
            order.append(i)
    return order


# ----------------------------------------------------------------------------- SVG

PALETTE = {
    "ext":    ("#ece6dc", "#b8ab92", "#3a3a36"),
    "gate":   ("#e8674c", "#b5402a", "#ffffff"),
    "shared": ("#cdd9c9", "#7d9478", "#2f3a2c"),
    "module": ("#dfe6ee", "#33445c", "#22303f"),
    "leaf":   ("#fbfaf7", "#c5bba6", "#2b2b28"),
    "root":   ("#33445c", "#22303f", "#ffffff"),
}
NAVY = "#33445c"
SAGE = "#5f7a59"
TAN = "#b8966a"
GREY = "#a99f88"


def build_svg(nodes, by_id, integ):
    W = 1320
    PAD_X = 26
    BAND_X = 210
    BAND_W = W - BAND_X - 210          # routing margins both sides
    CHIP_W, CHIP_H, CHIP_GAP = 196, 42, 12
    HEADER_H = 60
    BAND_GAP = 52

    modules = [n for n in nodes if n.get("depth") == 1]
    root = next((n for n in nodes if n.get("depth") == 0), None)
    parts_by_mod = {m["id"]: [c for c in nodes if c.get("parent") == m["id"]] for m in modules}

    # ---- data edges from integration-map wires (real targets after the arrow)
    data_edges = []          # (src_id, dst_id, label)
    for e in (integ or {}).get("edges", []):
        src = e.get("child")
        wires = e.get("wires", "") or ""
        before, _, after = wires.partition("->")
        targets = [t for t in re.findall(r"C-\d{3}", after) if t in by_id]
        lab = ""
        m = re.search(r"\.([A-Za-z_]+)", before)
        if m:
            lab = m.group(1)
        if not targets:
            targets = [e.get("parent")]
        for t in targets:
            if t in by_id and t != src:
                data_edges.append((src, t, lab))

    # ---- shared fan-out from reuse.known_consumers (authoritative)
    shared_edges = []        # (shared_id, consumer_id)
    for n in nodes:
        for cons in (n.get("reuse") or {}).get("known_consumers", []):
            if cons in by_id and cons != n["id"]:
                shared_edges.append((n["id"], cons))

    # ---- external inputs (contract inputs with no from_component)
    externals = {}           # name -> set(consumer ids)
    for n in nodes:
        for inp in (n.get("contract") or {}).get("inputs", []):
            if "from_component" not in inp:
                externals.setdefault(inp.get("name", "input"), set()).add(n["id"])

    # ---- module ordering by cross-module data edges (pipeline order)
    mod_ids = [m["id"] for m in modules]
    mod_edge_set = set()
    for s, d, _ in data_edges:
        ms, md = module_of(s, by_id), module_of(d, by_id)
        if ms in mod_ids and md in mod_ids and ms != md \
           and md != (root and root["id"]) and ms != (root and root["id"]):
            mod_edge_set.add((ms, md))
    ordered_mods = topo_order(mod_ids, mod_edge_set)

    # ---- vertical layout: external band, module bands, root band
    bands = {}               # id -> dict(x,y,w,h)
    chips = {}               # node id -> dict(x,y,w,h) for part chips
    y = 24

    # external band
    ext_names = list(externals.keys())
    cols_ext = max(1, BAND_W // (CHIP_W + CHIP_GAP))
    rows_ext = max(1, math.ceil(len(ext_names) / cols_ext)) if ext_names else 0
    ext_h = HEADER_H + rows_ext * (CHIP_H + CHIP_GAP) + 8 if ext_names else 0
    ext_band = {"x": BAND_X, "y": y, "w": BAND_W, "h": ext_h}
    ext_chip_pos = {}
    if ext_names:
        for i, nm in enumerate(ext_names):
            r, c = divmod(i, cols_ext)
            cx = BAND_X + 14 + c * (CHIP_W + CHIP_GAP)
            cy = y + HEADER_H - 16 + r * (CHIP_H + CHIP_GAP)
            ext_chip_pos[nm] = {"x": cx, "y": cy, "w": CHIP_W, "h": CHIP_H}
        y += ext_h + BAND_GAP

    band_index = {}
    idx = 0
    for mid in ordered_mods:
        kids = parts_by_mod.get(mid, [])
        cols = max(1, BAND_W // (CHIP_W + CHIP_GAP))
        rows = math.ceil(len(kids) / cols) if kids else 0
        h = HEADER_H + (rows * (CHIP_H + CHIP_GAP) + 8 if rows else 8)
        bands[mid] = {"x": BAND_X, "y": y, "w": BAND_W, "h": h}
        band_index[mid] = idx; idx += 1
        for j, k in enumerate(kids):
            r, c = divmod(j, cols)
            cx = BAND_X + 14 + c * (CHIP_W + CHIP_GAP)
            cy = y + HEADER_H - 8 + r * (CHIP_H + CHIP_GAP)
            chips[k["id"]] = {"x": cx, "y": cy, "w": CHIP_W, "h": CHIP_H}
        y += h + BAND_GAP

    root_band = None
    if root is not None:
        root_band = {"x": BAND_X, "y": y, "w": BAND_W, "h": 56}
        y += root_band["h"] + 24

    H = y + 8

    # ---- emit ------------------------------------------------------------------
    s = []
    s.append('<svg viewBox="0 0 %d %d" width="100%%" xmlns="http://www.w3.org/2000/svg" '
             'font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif" '
             'role="img" aria-label="Auto-laid-out component data-flow diagram">' % (W, H))
    # arrowhead markers
    for name, col in (("navy", NAVY), ("sage", SAGE), ("tan", TAN), ("grey", GREY)):
        s.append('<defs><marker id="ar-%s" markerWidth="9" markerHeight="9" refX="7" refY="3" '
                 'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="%s"/></marker></defs>' % (name, col))

    def band_anchor(b, side):
        if side == "top":
            return (b["x"] + b["w"] / 2, b["y"])
        if side == "bottom":
            return (b["x"] + b["w"] / 2, b["y"] + b["h"])
        if side == "left":
            return (b["x"], b["y"] + b["h"] / 2)
        return (b["x"] + b["w"], b["y"] + b["h"] / 2)   # right

    def edge_bus(p0, p1, busx, col, marker, dashed=False, label=""):
        x0, y0 = p0; x1, y1 = p1
        d = "M %.1f %.1f H %.1f V %.1f H %.1f" % (x0, y0, busx, y1, x1)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6"%s '
                 'marker-end="url(#ar-%s)" opacity="0.85"/>' % (d, col, dash, marker))
        if label:
            ly = (y0 + y1) / 2
            tw = len(label) * 6 + 8
            s.append('<rect x="%.1f" y="%.1f" width="%d" height="15" rx="2" fill="#fbfaf7" '
                     'stroke="%s" stroke-width="0.5" opacity="0.95"/>' % (busx - tw / 2, ly - 7.5, tw, col))
            s.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="%s" text-anchor="middle">%s</text>'
                     % (busx, ly + 2.5, col, esc(label)))

    def straight(p0, p1, col, marker, label=""):
        x0, y0 = p0; x1, y1 = p1
        midy = (y0 + y1) / 2
        d = "M %.1f %.1f C %.1f %.1f %.1f %.1f %.1f %.1f" % (x0, y0, x0, midy, x1, midy, x1, y1)
        s.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.2" '
                 'marker-end="url(#ar-%s)"/>' % (d, col, marker))
        if label:
            tw = len(label) * 6 + 10
            s.append('<rect x="%.1f" y="%.1f" width="%d" height="16" rx="2" fill="#fbfaf7" '
                     'stroke="%s" stroke-width="0.6"/>' % (x0 - tw / 2, midy - 8, tw, col))
            s.append('<text x="%.1f" y="%.1f" font-size="10" fill="%s" text-anchor="middle">%s</text>'
                     % (x0, midy + 3, col, esc(label)))

    # --- aggregate module->module data edges (exclude shared, handled separately)
    shared_pairs = set((module_of(a, by_id), module_of(b, by_id)) for a, b in shared_edges)
    agg = {}
    for sdid, ddid, lab in data_edges:
        ms, md = module_of(sdid, by_id), module_of(ddid, by_id)
        if ms not in band_index or md not in band_index or ms == md:
            continue
        agg.setdefault((ms, md), set())
        if lab:
            agg[(ms, md)].add(lab)

    # draw forward data edges first (right bus or straight spine)
    right_lane = 0
    left_lane = 0
    for (ms, md), labs in sorted(agg.items(), key=lambda kv: (band_index[kv[0][0]], band_index[kv[0][1]])):
        si, di = band_index[ms], band_index[md]
        label = ", ".join(sorted(labs))[:42]
        if di == si + 1:
            straight(band_anchor(bands[ms], "bottom"), band_anchor(bands[md], "top"), NAVY, "navy", label)
        elif di > si:
            busx = bands[ms]["x"] + bands[ms]["w"] + 26 + right_lane * 30
            right_lane = (right_lane + 1) % 5
            edge_bus(band_anchor(bands[ms], "right"), band_anchor(bands[md], "right"),
                     busx, NAVY, "navy", False, label)
        else:  # backward (up) — left bus
            busx = bands[ms]["x"] - 26 - left_lane * 30
            left_lane = (left_lane + 1) % 4
            edge_bus(band_anchor(bands[ms], "left"), band_anchor(bands[md], "left"),
                     busx, NAVY, "navy", False, label)

    # shared fan-out (green, left bus) from the shared chip/band to consumer band
    sl = 0
    for sid, cons in shared_edges:
        src_rect = chips.get(sid) or bands.get(module_of(sid, by_id))
        cmid = module_of(cons, by_id)
        if not src_rect or cmid not in bands:
            continue
        p0 = (src_rect["x"], src_rect["y"] + src_rect["h"] / 2)
        p1 = band_anchor(bands[cmid], "left")
        busx = BAND_X - 30 - (sl % 4) * 26
        sl += 1
        edge_bus(p0, p1, busx, SAGE, "sage", False, "")

    # external inputs (tan dashed) to consumer bands/root
    el = 0
    for nm, conss in externals.items():
        ep = ext_chip_pos.get(nm)
        if not ep:
            continue
        for cons in conss:
            cmid = module_of(cons, by_id)
            target = bands.get(cmid) or (root_band if cons == (root and root["id"]) else None)
            if not target:
                continue
            p0 = (ep["x"] + ep["w"], ep["y"] + ep["h"] / 2)
            p1 = band_anchor(target, "right")
            busx = target["x"] + target["w"] + 26 + (el % 5) * 30
            el += 1
            edge_bus(p0, p1, busx, TAN, "tan", True, "")

    # faint composition: each module hub -> root
    if root_band is not None:
        for mid in ordered_mods:
            x0, y0 = band_anchor(bands[mid], "bottom")
            x1, y1 = band_anchor(root_band, "top")
            s.append('<path d="M %.1f %.1f V %.1f" stroke="%s" stroke-width="1" '
                     'stroke-dasharray="2 5" opacity="0.25" fill="none"/>'
                     % (x0, y0, y1, GREY))

    # ---- band containers + headers + chips (drawn ON TOP of edges) -------------
    def container(b, title, sub, fill, stroke, txt, gate=False):
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="8" fill="%s" '
                 'stroke="%s" stroke-width="%s" opacity="0.97"/>'
                 % (b["x"], b["y"], b["w"], b["h"], fill, stroke, "2.4" if gate else "1.4"))
        s.append('<text x="%.1f" y="%.1f" font-size="14" font-weight="700" fill="%s">%s</text>'
                 % (b["x"] + 14, b["y"] + 26, txt, esc(title)))
        if sub:
            for i, ln in enumerate(wrap_text(sub, 96, 1)):
                s.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" opacity="0.85">%s</text>'
                         % (b["x"] + 14, b["y"] + 44 + i * 13, txt, esc(ln)))

    if ext_names:
        f, st, tx = PALETTE["ext"]
        container(ext_band, "External inputs", "values entering the pipeline from outside", "#f7f3ea", "#c9bfa6", "#6f6857")
        for nm, ep in ext_chip_pos.items():
            s.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="14" fill="%s" stroke="%s"/>'
                     % (ep["x"], ep["y"], ep["w"], ep["h"], f, st))
            for i, ln in enumerate(wrap_text(nm, 26, 2)):
                s.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" text-anchor="middle">%s</text>'
                         % (ep["x"] + ep["w"] / 2, ep["y"] + (16 if len(wrap_text(nm,26,2))==1 else 12) + i * 13 + 6, tx, esc(ln)))

    for mid in ordered_mods:
        m = by_id[mid]
        kind, shared, gate = classify(m)
        if gate:
            f, st, tx = "#fbeee9", "#e2a594", "#a8472f"
            container(bands[mid], "%s · %s" % (m["id"], m.get("name", "")),
                      m.get("single_responsibility", ""), f, "#e8674c", tx, gate=True)
        else:
            f, st, tx = "#f7f3ea", "#c9bfa6", "#33445c"
            container(bands[mid], "%s · %s" % (m["id"], m.get("name", "")),
                      m.get("single_responsibility", ""), f, st, "#5a5340")
        for k in parts_by_mod.get(mid, []):
            c = chips[k["id"]]
            kk, ksh, kg = classify(k)
            cf, cst, ctx = PALETTE["shared"] if ksh else PALETTE["leaf"]
            s.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="5" fill="%s" stroke="%s" '
                     'stroke-width="%s"/>' % (c["x"], c["y"], c["w"], c["h"], cf, cst, "1.8" if ksh else "1"))
            s.append('<text x="%.1f" y="%.1f" font-size="10.5" font-weight="700" fill="%s">%s%s</text>'
                     % (c["x"] + 8, c["y"] + 15, ctx, esc(k["id"]), " ◈" if ksh else ""))
            for i, ln in enumerate(wrap_text(k.get("name", ""), 30, 2)):
                s.append('<text x="%.1f" y="%.1f" font-size="9.5" fill="%s">%s</text>'
                         % (c["x"] + 8, c["y"] + 28 + i * 11, ctx, esc(ln)))

    if root_band is not None:
        f, st, tx = PALETTE["root"]
        s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="8" fill="%s" stroke="%s"/>'
                 % (root_band["x"], root_band["y"], root_band["w"], root_band["h"], f, st))
        s.append('<text x="%.1f" y="%.1f" font-size="14" font-weight="700" fill="%s">%s</text>'
                 % (root_band["x"] + 14, root_band["y"] + 24, tx,
                    esc("%s · %s (whole-product)" % (root["id"], root.get("name", "Product")))))
        s.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" opacity="0.85">%s</text>'
                 % (root_band["x"] + 14, root_band["y"] + 42, tx,
                    esc("all modules compose here; verified end-to-end against the vision")))

    s.append("</svg>")
    return "\n".join(s)


# ----------------------------------------------------------------------------- model extraction (shared by SVG + Mermaid)

def analyze(nodes, by_id, integ):
    """Return the data-flow model used by both diagram renderers."""
    modules = [n for n in nodes if n.get("depth") == 1]
    root = next((n for n in nodes if n.get("depth") == 0), None)
    parts_by_mod = {m["id"]: [c for c in nodes if c.get("parent") == m["id"]] for m in modules}

    data_edges = []
    for e in (integ or {}).get("edges", []):
        src = e.get("child")
        wires = e.get("wires", "") or ""
        before, _, after = wires.partition("->")
        targets = [t for t in re.findall(r"C-\d{3}", after) if t in by_id]
        lab = ""
        m = re.search(r"\.([A-Za-z_]+)", before)
        if m:
            lab = m.group(1)
        if not targets:
            targets = [e.get("parent")]
        for t in targets:
            if t in by_id and t != src:
                data_edges.append((src, t, lab))

    shared_edges = []
    for n in nodes:
        for cons in (n.get("reuse") or {}).get("known_consumers", []):
            if cons in by_id and cons != n["id"]:
                shared_edges.append((n["id"], cons))

    externals = {}
    for n in nodes:
        for inp in (n.get("contract") or {}).get("inputs", []):
            if "from_component" not in inp:
                externals.setdefault(inp.get("name", "input"), set()).add(n["id"])

    mod_ids = [m["id"] for m in modules]
    mod_edge_set = set()
    rid = root and root["id"]
    for s, d, _ in data_edges:
        ms, md = module_of(s, by_id), module_of(d, by_id)
        if ms in mod_ids and md in mod_ids and ms != md and md != rid and ms != rid:
            mod_edge_set.add((ms, md))
    ordered_mods = topo_order(mod_ids, mod_edge_set)
    return {
        "modules": modules, "root": root, "parts_by_mod": parts_by_mod,
        "data_edges": data_edges, "shared_edges": shared_edges,
        "externals": externals, "ordered_mods": ordered_mods,
    }


# ----------------------------------------------------------------------------- Mermaid (offline, exact connections diagram)

def mer_id(cid):
    return re.sub(r"\W", "", str(cid))


def mer_label(s):
    s = str(s)
    for a, b in (("&", " and "), ('"', "'"), ("<", "("), (">", ")"),
                 ("[", "("), ("]", ")"), ("|", "/"), ("{", "("), ("}", ")")):
        s = s.replace(a, b)
    return " ".join(s.split()).strip()


def mer_brk(text, width=16):
    """Sanitize + word-wrap into <br/>-joined lines (keeps Mermaid nodes narrow → vertical)."""
    words = mer_label(text).split()
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= width or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return "<br/>".join(lines) if lines else ""


def mer_node(cid, text, width=16):
    """id on its own line, then the wrapped name — short + narrow like the original diagram."""
    body = mer_brk(text, width)
    head = mer_label(cid)
    return (head + "<br/>" + body) if (head and body) else (head or body)


def real_externals(nodes, by_id):
    """Curated external entry points: an unwired contract input that is NOT supplied
    internally within its own module (which would make it plumbing, e.g. 'text').
    Root-level unwired inputs (the product's own entry, e.g. blog_idea) always count."""
    wired_in_module = {}
    for n in nodes:
        mid = module_of(n["id"], by_id)
        for inp in (n.get("contract") or {}).get("inputs", []):
            if "from_component" in inp:
                wired_in_module.setdefault(mid, set()).add(inp.get("name"))
    externals = {}
    for n in nodes:
        mid = module_of(n["id"], by_id)
        d = n.get("depth", 9)
        for inp in (n.get("contract") or {}).get("inputs", []):
            if "from_component" not in inp:
                nm = inp.get("name", "input")
                if d == 0 or nm not in wired_in_module.get(mid, set()):
                    externals.setdefault(nm, set()).add(n["id"])
    return externals


def build_mermaid(nodes, by_id, integ):
    """Curated, vertical connection diagram (matches the hand-authored original):
    one clean data-flow spine from correctly-directed wire edges only — no
    known_consumers fan-out (unreliable direction), no hub→child query back-edges,
    no root 'composition star'. Components grouped in subsystem subgraphs; the gate
    path is drawn thick; real external inputs enter dashed."""
    M = analyze(nodes, by_id, integ)
    root = M["root"]
    rid = root["id"] if root else None
    gate_ids = {n["id"] for n in nodes if classify(n)[2]}
    externals = real_externals(nodes, by_id)

    L = ["flowchart TB"]
    L += [
        "classDef ext fill:#ece6dc,stroke:#b8ab92,color:#3a3a36,font-style:italic;",
        "classDef gate fill:#e8674c,stroke:#b5402a,color:#ffffff;",
        "classDef shared fill:#cdd9c9,stroke:#7d9478,color:#2f3a2c;",
        "classDef module fill:#dfe6ee,stroke:#33445c,color:#22303f;",
        "classDef leaf fill:#fbfaf7,stroke:#c5bba6,color:#2b2b28;",
    ]
    # external input nodes (curated)
    ext_idm = {}
    for nm in externals:
        eid = "X_" + mer_id(nm)
        ext_idm[nm] = eid
        L.append('%s(["%s"]):::ext' % (eid, mer_brk(nm, 14)))
    # module subgraphs (pipeline order) with leaf children + hub — root omitted
    for mid in M["ordered_mods"]:
        if mid == rid:
            continue
        m = by_id[mid]
        kids = M["parts_by_mod"].get(mid, [])
        if kids:
            L.append('subgraph SG_%s["%s"]' % (mer_id(mid), mer_brk("%s · %s" % (m["id"], m.get("name", "")), 26)))
            L.append("direction TB")
            for k in kids:
                _, ksh, kg = classify(k)
                cls = "gate" if kg else ("shared" if ksh else "leaf")
                L.append('%s["%s"]:::%s' % (mer_id(k["id"]), mer_node(k["id"], k.get("name", ""), 16), cls))
            _, msh, mg = classify(m)
            hub = "gate" if mg else ("shared" if msh else "module")
            L.append('%s{{"%s"}}:::%s' % (mer_id(mid), mer_node(m["id"], m.get("name", ""), 16), hub))
            L.append("end")
        else:
            _, msh, mg = classify(m)
            cls = "gate" if mg else ("shared" if msh else "module")
            L.append('%s["%s"]:::%s' % (mer_id(mid), mer_node(m["id"], m.get("name", ""), 16), cls))

    # edges: ONLY correctly-directed wire data edges; exclude the root (composition,
    # not data flow). Gate-touching edges drawn thick.
    li = 0
    s_navy, s_thick, s_ext = [], [], []
    seen = set()
    for (s, d, lab) in M["data_edges"]:
        if s == rid or d == rid or s not in by_id or d not in by_id:
            continue
        if (s, d) in seen:
            continue
        seen.add((s, d))
        thick = (s in gate_ids) or (d in gate_ids)
        arrow = "==>" if thick else "-->"
        if lab:
            L.append("%s %s|%s| %s" % (mer_id(s), arrow, mer_label(lab), mer_id(d)))
        else:
            L.append("%s %s %s" % (mer_id(s), arrow, mer_id(d)))
        (s_thick if thick else s_navy).append(li); li += 1
    # external inputs enter dashed (skip edges into the omitted root)
    for nm, conss in externals.items():
        for c in conss:
            if c != rid and c in by_id:
                L.append("%s -.-> %s" % (ext_idm[nm], mer_id(c)))
                s_ext.append(li); li += 1

    def ls(idxs, css):
        if idxs:
            L.append("linkStyle %s %s" % (",".join(map(str, idxs)), css))
    ls(s_navy, "stroke:#33445c,stroke-width:1.6px;")
    ls(s_thick, "stroke:#e8674c,stroke-width:3px;")
    ls(s_ext, "stroke:#b8966a,stroke-width:1.4px,stroke-dasharray:5 4;")
    return "\n".join(L)


def explanation_cards(nodes):
    gate = [n for n in nodes if classify(n)[2]]
    shared = [n for n in nodes if classify(n)[1] and not classify(n)[2]]
    C = ['<div class="cards">']
    if gate:
        names = "; ".join("<code>%s</code> %s" % (esc(g["id"]), esc(g.get("name", ""))) for g in gate)
        C.append('<div class="card gate"><h4>Hard gate / choke point</h4>'
                 '<p>%s. <strong>Thick arrows</strong> trace the path through it — every relevant '
                 'input must pass through this component before downstream consumers see it. It '
                 'fails closed.</p></div>' % names)
    if shared:
        ids = ", ".join("<code>%s</code>" % esc(s["id"]) for s in shared)
        C.append('<div class="card shared"><h4>Shared components (◈, green)</h4>'
                 '<p>%s are each built <em>once</em> and consumed by several parents (you may see '
                 'more than one arrow leaving them). Building them early (as leaves) means every '
                 'consumer integrates against an already-verified dependency.</p></div>' % ids)
    C.append('<div class="card module"><h4>Reading the flow</h4>'
             '<p>Modules are stacked in <strong>pipeline order</strong> (topologically sorted by their '
             'cross-module data edges). Solid navy arrows are the main data path; <strong>dashed tan</strong> '
             'arrows are values entering from outside the system.</p></div>')
    C.append('<div class="card"><h4>Composition into the product</h4>'
             '<p>Every module ultimately composes into the whole-product root at the bottom, which is '
             'verified end-to-end against the vision — the final integration step of the build.</p></div>')
    C.append('</div>')
    return "".join(C)


# ----------------------------------------------------------------------------- HTML

def render_html(feature_dir):
    tree = load_json(os.path.join(feature_dir, "component-tree.json"), required=True)
    integ = load_json(os.path.join(feature_dir, "integration-map.json"), required=False) or {"edges": []}
    bplan = load_json(os.path.join(feature_dir, "build-plan.json"), required=False) or {}
    sc = load_json(os.path.join(feature_dir, "success-criteria.json"), required=False) or {}
    cov = load_json(os.path.join(feature_dir, "coverage_qa_report.json"), required=False) or {}
    vpath = os.path.join(feature_dir, "vision.md")
    vision = ""
    if os.path.isfile(vpath):
        with open(vpath, "r", encoding="utf-8") as fh:
            vision = fh.read()

    nodes = tree.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        die("component-tree.json: 'nodes' must be a non-empty list", 2)
    by_id = {n["id"]: n for n in nodes}

    product = tree.get("product_name") or tree.get("feature_id") or "Product"
    fid = tree.get("feature_id") or os.path.basename(feature_dir.rstrip("/"))
    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    leaves = [n for n in nodes if not (n.get("children") or [])]
    inter = [n for n in nodes if (n.get("children") or [])]
    shared_ct = sum(1 for n in nodes if (n.get("reuse") or {}).get("known_consumers"))
    maxdepth = max((n.get("depth", 0) for n in nodes), default=0)
    cov_status = cov.get("qa_status", "n/a")

    svg = build_svg(nodes, by_id, integ)
    # Component connection diagram (§3.2): prefer a curated, hand-tuned per-feature
    # override at planning/.../connections.mmd (used VERBATIM — this is the crisp,
    # human-authored diagram); otherwise generate one from the model. Rendered with
    # Mermaid v11 from CDN, so this diagram needs network (the rest stays offline).
    _override = os.path.join(feature_dir, "connections.mmd")
    if os.path.isfile(_override):
        with open(_override, "r", encoding="utf-8") as fh:
            mermaid_src = fh.read().strip()
    else:
        mermaid_src = build_mermaid(nodes, by_id, integ)

    P = []
    P.append("""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Plan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
 :root{--bg:#f4f0e8;--panel:#fbfaf7;--ink:#2b2b28;--muted:#6f6857;--rule:#d8cfba;
   --coral:#e8674c;--sage:#5f7a59;--navy:#33445c;--tan:#b8966a}
 *{box-sizing:border-box}
 html,body{margin:0;background:var(--bg);color:var(--ink);
   font-family:ui-serif,Georgia,'Times New Roman',serif;line-height:1.6}
 .doc{max-width:1180px;margin:0 auto;padding:0 28px 80px}
 header.top{padding:34px 0 18px;border-bottom:2px solid var(--ink);margin-bottom:8px}
 h1{font-size:34px;margin:0 0 6px;font-weight:700;letter-spacing:-.4px}
 h1 em{font-style:italic;color:var(--coral)}
 .meta{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;color:var(--muted)}
 .badges{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 4px}
 .badge{font-family:ui-sans-serif,system-ui,sans-serif;font-size:12px;padding:6px 12px;
   border:1px solid var(--rule);border-radius:3px;background:var(--panel)}
 .badge b{color:var(--navy)}
 .badge.ok{border-color:var(--sage);background:#eef3ec}
 h2{font-family:ui-sans-serif,system-ui,sans-serif;font-size:13px;letter-spacing:1.4px;
   text-transform:uppercase;color:var(--muted);margin:42px 0 8px;
   padding-bottom:6px;border-bottom:1px solid var(--rule)}
 h3{font-size:20px;margin:26px 0 6px}
 p{margin:8px 0}
 code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.86em;
   background:#efe9dc;padding:1px 5px;border-radius:3px;color:#4a4536}
 table{border-collapse:collapse;width:100%%;font-family:ui-sans-serif,system-ui,sans-serif;
   font-size:13px;margin:10px 0}
 th,td{border:1px solid var(--rule);padding:7px 9px;text-align:left;vertical-align:top}
 th{background:#efe9dc;font-weight:600}
 .diagram{background:var(--panel);border:1px solid var(--rule);border-radius:6px;
   padding:14px;overflow:auto;margin:12px 0}
 .legend{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0;
   font-family:ui-sans-serif,system-ui,sans-serif;font-size:12.5px}
 .legend .chip{display:flex;align-items:center;gap:7px;padding:5px 10px;
   border:1px solid var(--rule);border-radius:3px;background:var(--panel)}
 .sw{width:15px;height:15px;border-radius:2px;flex:none}
 .line{width:26px;height:0;flex:none;border-top-width:2px;border-top-style:solid}
 .howto{background:var(--panel);border-left:3px solid var(--navy);border-radius:3px;
   padding:12px 16px;font-family:ui-sans-serif,system-ui,sans-serif;font-size:13.5px}
 .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px;margin-top:12px}
 .card{background:var(--panel);border:1px solid var(--rule);border-radius:4px;
   padding:13px 15px;font-family:ui-sans-serif,system-ui,sans-serif;font-size:12.5px;line-height:1.5}
 .card.shared{border-left:3px solid var(--sage)}
 .card.gate{border-left:3px solid var(--coral)}
 .card.module{border-left:3px solid var(--navy)}
 .card h4{margin:0 0 2px;font-size:14px}
 .card .tag{display:inline-block;font-size:10px;letter-spacing:.6px;text-transform:uppercase;
   color:var(--muted);border:1px solid var(--rule);border-radius:2px;padding:1px 6px;margin-left:6px}
 .card dl{margin:7px 0 0;display:grid;grid-template-columns:auto 1fr;gap:2px 8px}
 .card dt{color:var(--muted);font-weight:600}
 .vision :is(h3,h4,h5){font-family:ui-sans-serif,system-ui,sans-serif}
 .note{font-family:ui-sans-serif,system-ui,sans-serif;font-size:12px;color:var(--muted);margin-top:6px}
 footer{margin-top:50px;padding-top:14px;border-top:1px solid var(--rule);
   font-family:ui-monospace,monospace;font-size:11.5px;color:var(--muted)}
</style></head><body><div class="doc">""" % esc(product))

    # header
    P.append('<header class="top"><h1>%s — <em>Plan</em></h1>'
             '<div class="meta">feature %s · %d components · generated %s · '
             'acos-genesis-protocol</div>' % (esc(product), esc(fid), len(nodes), esc(gen)))
    P.append('<div class="badges">')
    P.append('<div class="badge"><b>%d</b> components (%d leaves / %d intermediate)</div>'
             % (len(nodes), len(leaves), len(inter)))
    P.append('<div class="badge">max depth <b>%d</b></div>' % maxdepth)
    P.append('<div class="badge">shared units <b>%d</b></div>' % shared_ct)
    if sc.get("criteria"):
        P.append('<div class="badge">success criteria <b>%d</b></div>' % len(sc["criteria"]))
    cls = "badge ok" if str(cov_status).upper() == "APPROVED" else "badge"
    P.append('<div class="%s">coverage gate <b>%s</b></div>' % (cls, esc(cov_status)))
    P.append('</div></header>')

    # vision
    if vision.strip():
        P.append('<h2>1 · Vision</h2><div class="vision">%s</div>' % md_lite(vision))

    # success criteria
    if sc.get("criteria"):
        P.append('<h2>2 · Success Criteria</h2>')
        P.append('<table><tr><th>ID</th><th>Statement</th><th>How it is measured</th>'
                 '<th>Components</th></tr>')
        for c in sc["criteria"]:
            P.append('<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td><code>%s</code></td></tr>'
                     % (esc(c.get("id", "")), esc(c.get("statement", "")),
                        esc(c.get("measure", "")), esc(", ".join(c.get("covered_by", [])))))
        P.append('</table>')

    # diagrams — two complementary views
    P.append('<h2>3 · How the Components Connect</h2>')
    P.append('<p>Two complementary views of the same wiring. The <strong>pipeline data-flow</strong> '
             '(3.1) answers <em>"in what order does data move, stage to stage?"</em> — modules stacked '
             'top-to-bottom in build/pipeline order. The <strong>component connection diagram</strong> '
             '(3.2) answers <em>"how is each subsystem wired internally, and where are the gates and '
             'shared parts?"</em> — components grouped inside their subsystems with every connection drawn. '
             'Both are generated from <code>integration-map.json</code> + the component contracts.</p>')

    # 3.1 pipeline data-flow (pure-Python SVG)
    P.append('<h3>3.1 · Pipeline data-flow</h3>')
    P.append('<p>Stage view: each module is a band, its leaf components shown as chips. Read the '
             'solid navy arrows top-to-bottom to follow the main pipeline.</p>')
    P.append('<div class="legend">'
             '<div class="chip"><span class="sw" style="background:#ece6dc;border:1px solid #b8ab92"></span>External input</div>'
             '<div class="chip"><span class="sw" style="background:#fbeee9;border:1px solid #e8674c"></span>Hard gate / choke point</div>'
             '<div class="chip"><span class="sw" style="background:#cdd9c9;border:1px solid #7d9478"></span>Shared (◈) — many consumers</div>'
             '<div class="chip"><span class="sw" style="background:#f7f3ea;border:1px solid #c9bfa6"></span>Module band</div>'
             '<div class="chip"><span class="sw" style="background:#fbfaf7;border:1px solid #c5bba6"></span>Leaf chip</div>'
             '<div class="chip"><span class="line" style="border-color:#33445c"></span>Data edge</div>'
             '<div class="chip"><span class="line" style="border-color:#5f7a59"></span>Shared fan-out</div>'
             '<div class="chip"><span class="line" style="border-color:#b8966a;border-top-style:dashed"></span>External in</div>'
             '</div>')
    P.append('<div class="diagram">%s</div>' % svg)
    P.append('<div class="howto"><strong>How to read it.</strong> '
             'Follow the solid navy arrows top-to-bottom for the main pipeline. '
             'Green arrows are <em>shared components</em> fanning out to several consumers — '
             'built once, reused everywhere. Dashed tan arrows are values supplied from outside the system. '
             'The coral band is a <em>hard gate</em>: everything must pass through it. '
             'Faint dotted lines show every module composing into the whole-product root at the bottom.</div>')

    # 3.2 component connection diagram (Mermaid, offline-vendored)
    P.append('<h3>3.2 · Component connection diagram</h3>')
    P.append('<p>Connection view: components are grouped <em>inside</em> their subsystem boxes, with '
             'every data connection drawn. Use this to see internal wiring, the choke point '
             '(<strong>thick arrows</strong>), and how shared parts (◈) fan out.</p>')
    P.append('<div class="legend">'
             '<div class="chip"><span class="sw" style="background:#ece6dc;border:1px solid #b8ab92"></span>External input</div>'
             '<div class="chip"><span class="sw" style="background:#e8674c"></span>Hard gate (thick arrows pass through)</div>'
             '<div class="chip"><span class="sw" style="background:#cdd9c9;border:1px solid #7d9478"></span>Shared component (◈)</div>'
             '<div class="chip"><span class="sw" style="background:#dfe6ee;border:1px solid #33445c"></span>Module hub</div>'
             '<div class="chip"><span class="sw" style="background:#fbfaf7;border:1px solid #c5bba6"></span>Leaf component</div>'
             '<div class="chip"><span class="line" style="border-color:#33445c"></span>Data edge</div>'
             '<div class="chip"><span class="line" style="border-color:#b8966a;border-top-style:dashed"></span>External in</div>'
             '</div>')
    # Embedded verbatim (raw), exactly as the curated source — matches the original.
    P.append('<div class="diagram"><pre class="mermaid">\n%s\n</pre></div>' % mermaid_src)
    P.append(explanation_cards(nodes))

    # build plan
    if bplan.get("order") or bplan.get("levels"):
        P.append('<h2>4 · Build Plan (leaves-first)</h2>')
        if bplan.get("levels"):
            P.append('<p>Built bottom-up in phases — each component verified in isolation before '
                     'its parent composes it:</p><table><tr><th>Phase</th><th>Kind</th>'
                     '<th>Components</th></tr>')
            for i, lv in enumerate(bplan["levels"], 1):
                comp = lv.get("components", [])
                names = ", ".join(comp)
                P.append('<tr><td>%d (depth %s)</td><td>%s</td><td><code>%s</code></td></tr>'
                         % (i, esc(str(lv.get("depth", "?"))), esc(lv.get("kind", "")), esc(names)))
            P.append('</table>')
        if bplan.get("order"):
            P.append('<p class="note">Linear build order: <code>%s</code></p>'
                     % esc(" → ".join(bplan["order"])))
        rp = bplan.get("repair_protocol", {})
        if rp:
            P.append('<p><strong>Repair protocol.</strong> On a component failure, rework within '
                     'scope and re-run its isolated verifier (max <code>%s</code> iterations). On an '
                     'integration failure, drill <em>down</em> to the likely-culprit children, rebuild, '
                     're-verify, re-compose, and climb again (up→down→up).</p>'
                     % esc(str(rp.get("max_iterations_per_component", "n"))))

    # wiring table
    if integ.get("edges"):
        P.append('<h2>5 · Wiring Table (every connection)</h2>')
        P.append('<table><tr><th>From</th><th>To (parent/consumer)</th><th>Data / note</th></tr>')
        for e in integ["edges"]:
            P.append('<tr><td><code>%s</code></td><td><code>%s</code></td><td>%s</td></tr>'
                     % (esc(e.get("child", "")), esc(e.get("parent", "")),
                        esc(e.get("wires", "") + ((" — " + e["compose_note"]) if e.get("compose_note") else ""))))
        P.append('</table>')

    # component reference
    P.append('<h2>6 · Component Reference</h2>')
    P.append('<div class="cards">')
    for n in sorted(nodes, key=lambda x: x.get("build_order_index", 0)):
        kind, shared, gate = classify(n)
        cls = "card"
        if gate:
            cls += " gate"
        elif shared:
            cls += " shared"
        elif kind in ("module", "root"):
            cls += " module"
        tag = "ROOT" if kind == "root" else ("MODULE" if kind == "module" else "LEAF")
        if shared:
            tag += " · SHARED"
        if gate:
            tag += " · GATE"
        ct = n.get("contract") or {}
        ins = ", ".join(i.get("name", "") for i in ct.get("inputs", [])) or "—"
        outs = ", ".join(o.get("name", "") for o in ct.get("outputs", [])) or "—"
        ver = (n.get("verifier") or {}).get("type", "—")
        cons = ", ".join((n.get("reuse") or {}).get("known_consumers", []))
        P.append('<div class="%s"><h4>%s — %s<span class="tag">%s</span></h4>'
                 % (cls, esc(n.get("id", "")), esc(n.get("name", "")), esc(tag)))
        P.append('<p>%s</p>' % esc(n.get("purpose", "")))
        P.append('<dl>')
        P.append('<dt>in</dt><dd><code>%s</code></dd>' % esc(ins))
        P.append('<dt>out</dt><dd><code>%s</code></dd>' % esc(outs))
        P.append('<dt>verifier</dt><dd>%s</dd>' % esc(ver))
        P.append('<dt>build #</dt><dd>%s</dd>' % esc(str(n.get("build_order_index", "—"))))
        if cons:
            P.append('<dt>consumers</dt><dd><code>%s</code></dd>' % esc(cons))
        P.append('</dl></div>')
    P.append('</div>')

    P.append('<footer>Generated by acos-genesis-protocol · render-plan.py · §3.1 + content are offline; '
             '§3.2 renders via Mermaid v11 (CDN, needs network) · '
             'sources: component-tree.json, integration-map.json, build-plan.json, success-criteria.json, vision.md, connections.mmd</footer>')
    P.append('</div>')
    # Mermaid v11 from CDN — same engine + config as the original crisp diagram.
    P.append('<script type="module">'
             'import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";'
             'mermaid.initialize({startOnLoad:true,theme:"base",securityLevel:"loose",'
             'flowchart:{curve:"basis",nodeSpacing:38,rankSpacing:52,padding:8},'
             'themeVariables:{fontFamily:"Inter,ui-sans-serif,system-ui,sans-serif",fontSize:"13px",'
             'lineColor:"#9a8f78",primaryColor:"#fbfaf7",primaryTextColor:"#2b2b28",'
             'primaryBorderColor:"#c5bba6"}});'
             '</script>')
    P.append('</body></html>')
    return "".join(P)


def main(argv):
    args = [a for a in argv[1:] if a]
    if not args:
        die("usage: render-plan.py <feature-dir> [--out <path>]", 1)
    feature_dir = args[0]
    if not os.path.isdir(feature_dir):
        die("not a directory: %s" % feature_dir, 1)
    out = os.path.join(feature_dir, "plan.html")
    i = 1
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        else:
            i += 1
    html = render_html(feature_dir)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("RENDERED: %s  (%d bytes)" % (out, len(html)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
