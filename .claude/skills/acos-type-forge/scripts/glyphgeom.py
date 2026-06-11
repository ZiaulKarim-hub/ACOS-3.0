#!/usr/bin/env python3
"""Shared glyph<->Shapely geometry helpers for acos-type-forge.

The core insight of this skill: to remove/keep PARTS of a glyph you need a TRUE
geometric boolean (Shapely difference/intersection), NOT FontForge removeOverlap
(which FILLS empty regions of a reverse-wound rectangle, producing bars instead
of cuts on letters with gaps at the cut height, e.g. K, A, E).

Round-trip: TrueType quadratics --BasePen--> flat polygon rings --Shapely-->
result --TTGlyphPen--> TrueType outline written back into glyf.
"""
from fontTools.pens.basePen import BasePen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

DEFAULT_STEPS = 32


class FlattenPen(BasePen):
    """Decompose a glyph into flat polygon rings. BasePen converts TrueType
    quadratics into cubic _curveToOne calls, which we sample to line segments."""
    def __init__(self, glyphSet, steps=DEFAULT_STEPS):
        super().__init__(glyphSet)
        self.rings, self._c, self.steps = [], [], steps

    def _moveTo(self, p): self._c = [p]
    def _lineTo(self, p): self._c.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps; m = 1 - t
            self._c.append((
                m**3*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t**3*p3[0],
                m**3*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t**3*p3[1]))

    def _closePath(self):
        if len(self._c) >= 3:
            self.rings.append(self._c)
        self._c = []


def glyph_to_geom(glyphSet, gname, steps=DEFAULT_STEPS):
    """Return a Shapely (Multi)Polygon for the named glyph, holes included.
    Rings are combined with even-odd (symmetric_difference) so counters work."""
    fp = FlattenPen(glyphSet, steps)
    glyphSet[gname].draw(fp)
    geom = None
    for ring in fp.rings:
        poly = Polygon(ring).buffer(0)         # buffer(0) repairs self-touch/winding
        geom = poly if geom is None else geom.symmetric_difference(poly)
    return geom


def geom_to_pen(geom, pen):
    """Draw a Shapely geometry into a TTGlyphPen as all-on-curve contours.
    TrueType wants exterior clockwise, holes counter-clockwise -> orient(-1)."""
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        polys = [geom]
    elif hasattr(geom, "geoms"):
        polys = [g for g in geom.geoms if g.geom_type == "Polygon"]
    else:
        polys = []
    for poly in polys:
        if poly.is_empty:
            continue
        poly = orient(poly, -1.0)
        for ring in [poly.exterior, *poly.interiors]:
            pts = list(ring.coords)[:-1]
            if len(pts) < 3:
                continue
            pen.moveTo(pts[0])
            for p in pts[1:]:
                pen.lineTo(p)
            pen.closePath()


def write_glyph(font, gname, geom):
    """Replace a glyph's outline in the glyf table from a Shapely geometry."""
    glyf = font["glyf"]
    pen = TTGlyphPen(font.getGlyphSet())
    geom_to_pen(geom, pen)
    glyf[gname] = pen.glyph()
    glyf[gname].recalcBounds(glyf)
