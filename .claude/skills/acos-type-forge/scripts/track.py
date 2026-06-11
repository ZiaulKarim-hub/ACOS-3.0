#!/usr/bin/env fontforge
"""Tracking / metrics tweak — widen every glyph's side bearings uniformly
(the font-level cousin of CSS letter-spacing).

Run with FontForge's embedded Python (NOT system python):
  fontforge -lang=py -script track.py --in base.ttf --out tracked.ttf --track 30

Note: FontForge's side_bearing setters require INT; cast or they raise
'float object cannot be interpreted as an integer'.
"""
import fontforge, sys

def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag)+1] if flag in sys.argv else default

inp = arg("--in"); out = arg("--out"); track = int(arg("--track", "30"))
font = fontforge.open(inp)
n = 0
for g in font.glyphs():
    try:
        if g.isWorthOutputting() and len(g.foreground) > 0:
            g.left_side_bearing = int(round(g.left_side_bearing)) + track
            g.right_side_bearing = int(round(g.right_side_bearing)) + track
            n += 1
        elif g.width > 0:                       # empty glyphs (space) -> widen advance
            g.width = g.width + 2*track
    except Exception as e:
        print("  skip", g.glyphname, e)
print("tracked glyphs:", n)
font.generate(out)
print("wrote", out)
