#!/usr/bin/env python3
"""Static server for the editor + a POST /save endpoint that writes the project
to disk (edits/glyph-edits.json), so the editor's Save button is a real save —
not just browser localStorage. vectorize.py reads that file directly.

Run via serve.sh (which first builds assets/base.woff2). Or:
  python3 serve.py <assets_dir> <edits_dir> <port>
"""
import http.server, os, sys, json

ASSETS = sys.argv[1] if len(sys.argv) > 1 else "assets"
EDITS  = sys.argv[2] if len(sys.argv) > 2 else "edits"
PORT   = int(sys.argv[3]) if len(sys.argv) > 3 else 8787

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ASSETS, **k)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*"); super().end_headers()
    def do_POST(self):
        if self.path.rstrip("/") == "/save":
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                json.loads(body)                       # validate
                os.makedirs(EDITS, exist_ok=True)
                with open(os.path.join(EDITS, "glyph-edits.json"), "wb") as f:
                    f.write(body)
                self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
            except Exception as e:
                self.send_response(400); self.end_headers(); self.wfile.write(str(e).encode())
        else:
            self.send_response(404); self.end_headers()

os.makedirs(EDITS, exist_ok=True)
print(f"editor:  http://127.0.0.1:{PORT}/editor.html")
print(f"save ->  {os.path.abspath(EDITS)}/glyph-edits.json")
http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
