#!/usr/bin/env python3
"""Type-Forge unified server — one port serves the whole app.

Pages (all same origin, relative links):
  /                home hub
  /editor.html     glyph paint editor   (font: base.woff2 = the base typeface)
  /spacing.html    spacing editor       (font: font.woff2 = current built font)
  /specimen.html   specimen viewer      (font: font.woff2)

Data endpoints:
  GET  /base.woff2 /font.woff2          fonts
  GET  /metrics.json                    baked per-glyph L/R/advance (for spacing)
  GET  /charset.json                    every glyph in the font, grouped (for specimen)
  GET  /glyph-edits.json                disk glyph edits (editor loads these on a fresh origin)
  GET/POST /spacing.json                per-glyph cushion overrides
  POST /save                            write glyph-edits.json

Run via typeforge.sh, or:
  python3 typeforge_serve.py <base.ttf> <built.ttf> <edits_dir> <assets_dir> <port>
"""
import http.server, os, sys, json, shutil
from fontTools.ttLib import TTFont

BASE_TTF  = sys.argv[1]
BUILT_TTF = sys.argv[2]
EDITS     = sys.argv[3]
ASSETS    = sys.argv[4]
PORT      = int(sys.argv[5]) if len(sys.argv) > 5 else 8800

SERVE = os.path.join(os.path.dirname(os.path.abspath(BUILT_TTF)), "_typeforge")
os.makedirs(SERVE, exist_ok=True)
GLYPH_JSON   = os.path.join(EDITS, "glyph-edits.json")
SPACING_JSON = os.path.join(EDITS, "spacing.json")

# --- pages ---
for page in ("home.html", "editor.html", "spacing.html", "specimen.html"):
    src = os.path.join(ASSETS, page)
    if os.path.exists(src):
        shutil.copy(src, os.path.join(SERVE, page))
# serve home at "/"
shutil.copy(os.path.join(ASSETS, "home.html"), os.path.join(SERVE, "index.html"))

# --- fonts ---
def to_woff2(ttf, out):
    f = TTFont(ttf); f.flavor = "woff2"; f.save(out)
to_woff2(BASE_TTF,  os.path.join(SERVE, "base.woff2"))
to_woff2(BUILT_TTF, os.path.join(SERVE, "font.woff2"))

# --- metrics (spacing) + charset (specimen) from the built font ---
f = TTFont(BUILT_TTF); cmap = f.getBestCmap(); glyf = f["glyf"]; hmtx = f["hmtx"]; upm = f["head"].unitsPerEm
SPACE_CHARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;!?'\"()-/&@#%=+")
metrics = {"upm": upm, "glyphs": {}}
for ch in SPACE_CHARS:
    o = ord(ch)
    if o not in cmap: continue
    gn = cmap[o]; gl = glyf[gn]; adv, lsb = hmtx[gn]
    if getattr(gl, "numberOfContours", 0) > 0:
        metrics["glyphs"][ch] = [int(gl.xMin), int(adv - gl.xMax), int(adv)]
    else:
        metrics["glyphs"][ch] = [int(lsb), int(adv - lsb), int(adv)]
json.dump(metrics, open(os.path.join(SERVE, "metrics.json"), "w"))

# every printable character the font actually has a glyph for, grouped
def categorize(ch):
    o = ord(ch)
    if ch.isdigit(): return "Numbers"
    if ch.isupper(): return "Uppercase" if o < 128 else "Uppercase — accented"
    if ch.islower(): return "Lowercase" if o < 128 else "Lowercase — accented"
    return "Punctuation & symbols"
ORDER = ["Uppercase", "Lowercase", "Numbers", "Punctuation & symbols",
         "Uppercase — accented", "Lowercase — accented"]
groups = {k: [] for k in ORDER}
for o in sorted(cmap.keys()):
    if o < 0x20 or (0x7f <= o < 0xa0): continue          # skip control chars
    try: ch = chr(o)
    except ValueError: continue
    if not ch.isprintable() or ch == " ": continue
    groups.setdefault(categorize(ch), []).append(ch)
charset = {"groups": [{"name": k, "chars": "".join(groups[k])} for k in ORDER if groups.get(k)]}
json.dump(charset, open(os.path.join(SERVE, "charset.json"), "w"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=SERVE, **k)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _send_json_file(self, path):
        data = open(path, "rb").read() if os.path.exists(path) else b"{}"
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        p = self.path.split("?")[0].rstrip("/")
        if p in ("", "/"):       self.path = "/index.html"; return super().do_GET()
        if p == "/spacing.json":     return self._send_json_file(SPACING_JSON)
        if p == "/glyph-edits.json": return self._send_json_file(GLYPH_JSON)
        return super().do_GET()

    def do_POST(self):
        p = self.path.rstrip("/")
        target = {"/save": GLYPH_JSON, "/spacing.json": SPACING_JSON}.get(p)
        if not target:
            self.send_response(404); self.end_headers(); return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            json.loads(body)
            os.makedirs(EDITS, exist_ok=True)
            with open(target, "wb") as fp: fp.write(body)
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        except Exception as e:
            self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())


print(f"Type-Forge → http://127.0.0.1:{PORT}/")
print(f"  glyph edits  -> {GLYPH_JSON}")
print(f"  spacing      -> {SPACING_JSON}")
http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
