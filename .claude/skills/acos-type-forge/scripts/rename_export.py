#!/usr/bin/env python3
"""OFL-compliant rename + multi-format export.

OFL 1.1 lets you modify and redistribute, with ONE rule: drop the base font's
Reserved Font Name from your derivative's name (keep it only in the required
copyright/attribution). This scrubs the reserved name everywhere except nameID 0,
renames family/full/PostScript + CFF, and emits TTF + WOFF2 (+ OTF if input is
CFF) plus a FONTLOG.

Usage:
  python3 rename_export.py --in staged.ttf --family "My Titling" \
      --reserved Cinzel --base "Cinzel Decorative" --author "Natanael Gama" \
      --year 2026 --owner "Your Foundry" --out-dir build/ --mods "tracking; stencil cut O K A"
"""
import argparse, os
from fontTools.ttLib import TTFont

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--family", required=True, help="new family name (must NOT contain the reserved name)")
    ap.add_argument("--reserved", required=True, help="Reserved Font Name of the base, e.g. Cinzel")
    ap.add_argument("--base", required=True, help="base family, e.g. 'Cinzel Decorative'")
    ap.add_argument("--author", default="the original author")
    ap.add_argument("--year", default="2026")
    ap.add_argument("--owner", default="You")
    ap.add_argument("--out-dir", default="build")
    ap.add_argument("--mods", default="modified")
    ap.add_argument("--ofl", help="path to the base OFL.txt to copy alongside")
    a = ap.parse_args()

    assert a.reserved.lower() not in a.family.lower(), \
        f"OFL violation: new family '{a.family}' must not contain reserved name '{a.reserved}'"
    os.makedirs(a.out_dir, exist_ok=True)
    ps = a.family.replace(" ", "") + "-Regular"
    ver = "1.000"
    copyright_ = (f"Copyright {a.year} {a.owner}. {a.family} is a derivative of "
                  f"{a.base} (Copyright {a.author}), used under the SIL Open Font "
                  f"License 1.1. '{a.reserved}' is a Reserved Font Name of the original.")
    NAMES = {0: copyright_, 1: a.family, 2: "Regular", 3: f"{a.family} {ver}",
             4: a.family, 6: ps, 16: a.family, 17: "Regular"}

    f = TTFont(a.inp); nm = f["name"]
    for nid, val in NAMES.items():
        nm.setName(val, nid, 3, 1, 0x409); nm.setName(val, nid, 1, 0, 0)
    for rec in nm.names:                                  # scrub residual reserved name
        s = rec.toUnicode()
        if a.reserved in s and rec.nameID not in NAMES:
            rec.string = s.replace(a.base, a.family).replace(a.reserved, a.family)
    is_cff = "CFF " in f
    if is_cff:
        cff = f["CFF "].cff; old = cff.fontNames[0]; td = cff[old]
        for attr in ("FullName", "FamilyName"):
            if hasattr(td, attr): setattr(td, attr, a.family)
        cff.fontNames[0] = ps

    base = os.path.join(a.out_dir, ps)
    f.save(base + (".otf" if is_cff else ".ttf"))
    # always emit a TTF + WOFF2 for the web (from the saved file)
    g = TTFont(base + (".otf" if is_cff else ".ttf"))
    if not is_cff:
        g.flavor = "woff2"; g.save(base + ".woff2")
    else:
        g.flavor = "woff2"; g.save(base + ".woff2")
    # residual check
    hits = [r.nameID for r in TTFont(base + (".otf" if is_cff else ".ttf"))["name"].names
            if a.reserved in r.toUnicode() and r.nameID != 0]
    print(f"family='{a.family}'  reserved-name leaks (excl. copyright id0): {hits or 'NONE'}")
    with open(os.path.join(a.out_dir, "FONTLOG.txt"), "w") as fp:
        fp.write(f"{a.family}\n{'='*len(a.family)}\n\nA derivative of {a.base} ({a.author}), "
                 f"under SIL OFL 1.1.\nModifications: {a.mods}.\n'{a.reserved}' is a Reserved "
                 f"Font Name; this derivative is renamed per OFL.\n")
    if a.ofl and os.path.exists(a.ofl):
        import shutil; shutil.copy(a.ofl, os.path.join(a.out_dir, "OFL.txt"))
    print("exported to", a.out_dir, "(+ FONTLOG.txt" + (", OFL.txt" if a.ofl else "") + ")")

if __name__ == "__main__":
    main()
