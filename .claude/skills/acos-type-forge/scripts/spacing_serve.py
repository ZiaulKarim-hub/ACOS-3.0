#!/usr/bin/env python3
"""Server for the browser Spacing Editor.

Serves spacing.html + the current font (as woff2) + the font's BAKED per-glyph
metrics (metrics.json), and reads/writes the user's per-glyph cushion overrides
(spacing.json) to disk. vectorize.py --spacing-file <that file> bakes them in.

The editor previews cushions live by nudging each letter's CSS margins by
(chosen - baked) units, so no rebuild is needed to SEE spacing; a rebuild only
bakes it into the real font.

Run via spacing.sh, or:
  python3 spacing_serve.py <font.ttf> <assets_dir> <edits_dir> <port>
"""
import http.server, os, sys, json
from fontTools.ttLib import TTFont

FONT   = sys.argv[1]
ASSETS = sys.argv[2] if len(sys.argv) > 2 else "assets"
EDITS  = sys.argv[3] if len(sys.argv) > 3 else "edits"
PORT   = int(sys.argv[4]) if len(sys.argv) > 4 else 8790

SERVE = os.path.join(os.path.dirname(os.path.abspath(FONT)), "_spacing")
os.makedirs(SERVE, exist_ok=True)
SPACING_JSON = os.path.join(EDITS, "spacing.json")

# --- copy the editor page in ---
import shutil
shutil.copy(os.path.join(ASSETS, "spacing.html"), os.path.join(SERVE, "spacing.html"))

# --- font -> woff2 for the page, and compute baked metrics ---
f = TTFont(FONT)
f.flavor = "woff2"; f.save(os.path.join(SERVE, "spacingfont.woff2"))
f2 = TTFont(FONT)                                  # fresh (save() mutated flavor)
cmap = f2.getBestCmap(); glyf = f2["glyf"]; hmtx = f2["hmtx"]
upm = f2["head"].unitsPerEm
CHARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
         "abcdefghijklmnopqrstuvwxyz"
         "0123456789"
         ".,:;!?'\"()-/&@#%=+")
metrics = {"upm": upm, "glyphs": {}}
for ch in CHARS:
    o = ord(ch)
    if o not in cmap:
        continue
    gn = cmap[o]; gl = glyf[gn]; adv, lsb = hmtx[gn]
    if getattr(gl, "numberOfContours", 0) > 0:
        rsb = adv - gl.xMax
        metrics["glyphs"][ch] = [int(gl.xMin), int(rsb), int(adv)]
    else:
        metrics["glyphs"][ch] = [int(lsb), int(adv - lsb), int(adv)]
json.dump(metrics, open(os.path.join(SERVE, "metrics.json"), "w"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=SERVE, **k)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/"):
            self.path = "/spacing.html"
        if self.path.split("?")[0] == "/spacing.json":
            data = b"{}"
            if os.path.exists(SPACING_JSON):
                data = open(SPACING_JSON, "rb").read()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(data); return
        return super().do_GET()

    def do_POST(self):
        if self.path.rstrip("/") == "/spacing.json":
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                json.loads(body)                          # validate
                os.makedirs(EDITS, exist_ok=True)
                with open(SPACING_JSON, "wb") as fp:
                    fp.write(body)
                self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())
        else:
            self.send_response(404); self.end_headers()


print(f"spacing editor: http://127.0.0.1:{PORT}/spacing.html")
print(f"save -> {SPACING_JSON}")
http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
