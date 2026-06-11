#!/usr/bin/env python3
"""Stencil-cut a horizontal band out of chosen glyphs via TRUE geometric
difference (Shapely). Unlike FontForge removeOverlap this only removes where ink
exists -> clean gaps on K / A / E, never fill bars.

Usage:
  python3 cut.py --in base.ttf --out cut.ttf --letters OKA --y0 318 --y1 382
"""
import argparse, os, sys
from fontTools.ttLib import TTFont
from shapely.geometry import box
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyphgeom import glyph_to_geom, write_glyph

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--letters", required=True, help="characters to cut, e.g. OKA")
    ap.add_argument("--y0", type=float, required=True, help="band bottom (font units, em=1000)")
    ap.add_argument("--y1", type=float, required=True, help="band top")
    ap.add_argument("--pad", type=float, default=100, help="horizontal overshoot (safe: true diff)")
    a = ap.parse_args()

    f = TTFont(a.inp); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    for ch in a.letters:
        gname = cmap[ord(ch)]
        geom = glyph_to_geom(gs, gname)
        x0, _, x1, _ = geom.bounds
        band = box(x0 - a.pad, a.y0, x1 + a.pad, a.y1)
        res = geom.difference(band)
        write_glyph(f, gname, res)
        print(f"  cut {ch!r}: area {geom.area:.0f} -> {res.area:.0f}")
    f.save(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
