#!/usr/bin/env python3
"""Remove FOOT serifs by cross-section extrusion (Shapely). Samples each stroke's
width just above the serif, keeps only those stem columns below that line ->
deletes the flared bracket + overhanging foot, stem ends flat.

ONLY safe for clean vertical-stem letters (default AFHIKMNPRT). Letters with a
bowl (B D) or horizontal bottom arm (E L Z) need per-letter handling; round /
pointed letters (C G J O Q S U V W X Y) have no foot serif.

Usage:
  python3 strip_serifs.py --in base.ttf --out noserif.ttf --letters AFHIKMNPRT --serif-h 116
"""
import argparse, os, sys
from fontTools.ttLib import TTFont
from shapely.geometry import box, LineString
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyphgeom import glyph_to_geom, write_glyph

def intervals_at(geom, y, xmin, xmax):
    inter = geom.intersection(LineString([(xmin-300, y), (xmax+300, y)]))
    out = []
    if inter.is_empty: return out
    parts = list(inter.geoms) if hasattr(inter, "geoms") else [inter]
    for s in parts:
        if s.geom_type != "LineString" or s.is_empty: continue   # skip tangent points
        xs = [c[0] for c in s.coords]
        if xs: out.append((min(xs), max(xs)))
    return out

def strip(geom, serif_h):
    xmin, ymin, xmax, ymax = geom.bounds
    cols = intervals_at(geom, ymin + serif_h, xmin, xmax)
    if not cols: return geom
    pillars = [box(a, ymin-40, b, ymin+serif_h) for a, b in cols]
    above = box(xmin-50, ymin+serif_h, xmax+50, ymax+50)
    return geom.intersection(unary_union(pillars + [above]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--letters", default="AFHIKMNPRT")
    ap.add_argument("--serif-h", type=float, default=116, help="serif-zone height (font units)")
    a = ap.parse_args()
    f = TTFont(a.inp); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    for ch in a.letters:
        gname = cmap[ord(ch)]
        geom = glyph_to_geom(gs, gname)
        write_glyph(f, gname, strip(geom, a.serif_h))
        print(f"  stripped foot serif: {ch!r}")
    f.save(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
