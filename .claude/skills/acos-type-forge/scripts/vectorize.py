#!/usr/bin/env python3
"""Bridge editor raster edits -> real glyph outlines via potrace, written back
into the font. Closes the loop: paint in the browser, rebuild an installable font.

Accepts the editor's "Export all edits (.json)" (dict char->dataURL) OR a folder
of PNGs named like NAME-<CHAR>.png / <CHAR>.png.

Pixel->unit mapping must match the editor canvas: --em (px per em, = editor SIZE)
and --baseline (px, = editor BASE). Outlines are traced, mapped to font units,
and re-seated to each glyph's original left side bearing + advance (metrics kept).

Usage:
  python3 vectorize.py --base base.ttf --edits glyph-edits.json \
      --out edited.ttf --em 620 --baseline 740
"""
import argparse, base64, glob, json, os, re, subprocess, sys, tempfile
from fontTools.ttLib import TTFont
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from shapely.affinity import translate as shp_translate
from shapely.affinity import scale as shp_scale
from shapely.geometry import Polygon
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyphgeom import write_glyph, FlattenPen

def load_edits(path):
    """Return {char: PIL.Image RGBA}."""
    out = {}
    if path.endswith(".json"):
        data = json.load(open(path))
        for ch, url in data.items():
            b = base64.b64decode(url.split(",", 1)[1])
            out[ch] = Image.open(__import__("io").BytesIO(b)).convert("RGBA")
    else:
        for fn in glob.glob(os.path.join(path, "*.png")):
            ch = re.split(r"[-_]", os.path.splitext(os.path.basename(fn))[0])[-1]
            if len(ch) == 1:
                out[ch] = Image.open(fn).convert("RGBA")
    return out

def trace_to_geom(img, em, baseline):
    """potrace the bitmap, return a Shapely geometry in font units."""
    # composite over white, threshold to 1-bit (potrace traces black on white)
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255)); bg.alpha_composite(img)
    bw = bg.convert("L").point(lambda v: 0 if v < 128 else 255, mode="1")
    with tempfile.TemporaryDirectory() as td:
        pbm = os.path.join(td, "g.bmp"); svgf = os.path.join(td, "g.svg")
        bw.save(pbm)
        subprocess.run(["potrace", "-b", "svg", "--flat", "-o", svgf, pbm], check=True)
        svg = open(svgf).read()
    m = re.search(r'transform="translate\(([-\d.]+),([-\d.]+)\)\s*scale\(([-\d.]+),([-\d.]+)\)"', svg)
    if not m: raise RuntimeError("unexpected potrace SVG transform")
    e, f, a, d = map(float, m.groups())
    s = 1000.0 / em
    # SVG path pt (px,py) -> font units:  fx = s*(a*px+e),  fy = s*(baseline-(d*py+f))
    affine = (s*a, 0, 0, -s*d, s*e, s*(baseline - f))
    # parse_path -> TransformPen -> FlattenPen: properly SAMPLES potrace's cubic
    # beziers (not just dumping control points), and the affine has positive
    # determinant so potrace's contour winding is preserved.
    fp = FlattenPen({}, steps=24)
    tp = TransformPen(fp, affine)
    for d_ in re.findall(r'<path[^>]*\bd="([^"]+)"', svg):
        parse_path(d_, tp)
    geom = None
    for r in fp.rings:
        poly = Polygon(r).buffer(0)
        geom = poly if geom is None else geom.symmetric_difference(poly)
    return geom

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--edits", required=True, help=".json from editor OR folder of PNGs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--em", type=float, default=620, help="editor SIZE (px per em)")
    ap.add_argument("--baseline", type=float, default=740, help="editor BASE (px)")
    ap.add_argument("--space", type=float, default=None,
                    help="auto-space edited glyphs: set LSB=RSB=this many font units "
                         "and advance=ink_width+2*space (overrides metrics-preserving). "
                         "Fixes touching letters. Try 80 (=8%% of a 1000-unit em).")
    ap.add_argument("--lc-scale", type=float, default=None,
                    help="scale lowercase glyphs (a-z, accented incl.) by this factor "
                         "about the baseline — e.g. 0.75 makes small-caps smaller. "
                         "Best combined with --space so advances follow the new size.")
    ap.add_argument("--uc-space", type=float, default=None,
                    help="separate sidebearing for UPPERCASE A-Z (overrides --space "
                         "for caps only). Use when caps read looser than lowercase — "
                         "e.g. --space 30 --uc-space 10. Enables auto-spacing on its own; "
                         "letters not covered fall back to --space (or a default).")
    ap.add_argument("--lc-space", type=float, default=None,
                    help="separate sidebearing for lowercase a-z (overrides --space for "
                         "lowercase only). With --lc-scale, small-caps need a smaller "
                         "sidebearing than --space so cap/small-cap junctions don't gape. "
                         "e.g. --space 30 --uc-space 10 --lc-space 12. Enables auto-spacing "
                         "on its own; uncovered letters fall back to --space (or a default).")
    ap.add_argument("--letter-space", default=None,
                    help="per-glyph sidebearing override(s). Format: 'CHARS:VALUE' groups "
                         "joined by commas, e.g. 'ANRUVWX:0,M:5'. Diagonal/open letters "
                         "(A V W X N R U) often need this below the uppercase default. "
                         "Negative is allowed. Enables auto-spacing on its own; uncovered "
                         "letters fall back to --space (or a default).")
    ap.add_argument("--spacing-file", default=None,
                    help="JSON {char:[lsb,rsb]} of EXACT independent per-glyph sidebearings "
                         "(written by the browser Spacing Editor). Highest priority of all "
                         "spacing controls. Enables auto-spacing on its own; letters not "
                         "listed fall back to --space (or a default when --space is omitted).")
    a = ap.parse_args()
    # Any spacing flag (not just --space) triggers the auto-space branch. This lets
    # --spacing-file (or --uc-space/--lc-space/--letter-space) be passed ALONE: when
    # --space is omitted we fall back to DEFAULT_SPACE for letters not otherwise
    # covered, instead of silently ignoring the flag and keeping original metrics.
    DEFAULT_SPACE = 80.0
    spacing_active = (a.space is not None or a.uc_space is not None
                      or a.lc_space is not None or a.letter_space is not None
                      or a.spacing_file is not None)
    space_fallback = a.space if a.space is not None else DEFAULT_SPACE
    f = TTFont(a.base); cmap = f.getBestCmap(); glyf = f["glyf"]; hmtx = f["hmtx"]
    # Inherited kerning (GPOS 'kern' / legacy 'kern' table) was tuned for the
    # ORIGINAL glyph widths. Once we re-space (--space) or scale (--lc-scale),
    # those pairs are wrong and cause overlaps — e.g. Cinzel kerns h-e by -337,
    # which swallows our sidebearings and fuses "he". Drop kerning so rendered
    # text honors the clean sidebearings we just set.
    if spacing_active or a.lc_scale is not None:
        for tag in ("GPOS", "kern"):
            if tag in f:
                del f[tag]; print(f"  stripped inherited {tag} (invalid after re-spacing)")
    # per-glyph sidebearing overrides (e.g. "ANRUVWX:0,M:5")
    ls = {}
    if a.letter_space:
        for grp in a.letter_space.split(","):
            chars, val = grp.split(":")
            for c in chars.strip():
                ls[c] = float(val)
    # exact independent per-glyph sidebearings from the Spacing Editor
    sf = {}
    if a.spacing_file and os.path.exists(a.spacing_file):
        for k, v in json.load(open(a.spacing_file)).items():
            sf[k] = (float(v[0]), float(v[1]))
        print(f"  spacing-file: {len(sf)} per-glyph overrides loaded")
    edits = load_edits(a.edits)
    for ch, img in edits.items():
        if ord(ch) not in cmap:
            print("  skip (not in font):", ch); continue
        gname = cmap[ord(ch)]
        geom = trace_to_geom(img, a.em, a.baseline)
        if geom is None or geom.is_empty:
            print("  empty trace:", ch); continue
        if a.lc_scale is not None and ch.islower():
            # shrink lowercase about the baseline (y=0) so they read as small-caps
            geom = shp_scale(geom, xfact=a.lc_scale, yfact=a.lc_scale, origin=(0, 0))
        adv, lsb = hmtx[gname]                       # original metrics
        if not spacing_active:
            # metrics-preserving: re-seat to original LSB, keep original advance
            ox = glyf[gname].xMin if hasattr(glyf[gname], "xMin") else lsb
            geom = shp_translate(geom, xoff=ox - geom.bounds[0])
            write_glyph(f, gname, geom)
            hmtx[gname] = (adv, glyf[gname].xMin)
            print(f"  vectorized {ch!r}")
        else:
            # auto-space: seat ink with independent left/right cushions, advance =
            # ink_width + lsb + rsb. Priority: spacing-file (independent L/R) >
            # per-glyph override (symmetric) > uppercase default > general --space.
            if ch in sf:
                lsb_t, rsb_t = sf[ch]
            elif ch in ls:
                lsb_t = rsb_t = ls[ch]
            elif a.uc_space is not None and ch.isupper():
                lsb_t = rsb_t = a.uc_space
            elif a.lc_space is not None and ch.islower():
                lsb_t = rsb_t = a.lc_space
            else:
                lsb_t = rsb_t = space_fallback
            geom = shp_translate(geom, xoff=lsb_t - geom.bounds[0])
            write_glyph(f, gname, geom)
            ink_w = geom.bounds[2] - geom.bounds[0]
            new_adv = int(round(ink_w + lsb_t + rsb_t))
            hmtx[gname] = (new_adv, glyf[gname].xMin)
            print(f"  vectorized {ch!r}  (adv {adv}->{new_adv}, L{lsb_t:g}/R{rsb_t:g})")
    f.save(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
