#!/usr/bin/env python3
"""Assemble a single self-contained HTML: OKOA tokens + layout CSS inlined,
fonts embedded as base64 data: URIs. Output: zermatt-credit-memo.html"""
import base64, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

FACES = [
    ("Inter", 400, "Inter-Regular.ttf"),
    ("Inter", 300, "Inter-Light.ttf"),
    ("Inter", 500, "Inter-Medium.ttf"),
    ("Inter", 600, "Inter-SemiBold.ttf"),
    ("Inter Display", 300, "InterDisplay-Light.ttf"),
    ("Inter Display", 400, "InterDisplay-Regular.ttf"),
    ("Cormorant Garamond", 400, "CormorantGaramond-Regular.ttf"),
    ("Cormorant Garamond", 500, "CormorantGaramond-Medium.ttf"),
    ("Cormorant Garamond", 600, "CormorantGaramond-SemiBold.ttf"),
    ("JetBrains Mono", 400, "JetBrainsMono-Regular.ttf"),
    ("JetBrains Mono", 500, "JetBrainsMono-Medium.ttf"),
    ("JetBrains Mono", 600, "JetBrainsMono-SemiBold.ttf"),
]

def datauri(fn):
    b = open(os.path.join("fonts", fn), "rb").read()
    return "data:font/ttf;base64," + base64.b64encode(b).decode()

font_css = "\n".join(
    f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
    f"src:url({datauri(fn)}) format('truetype');font-display:swap;}}"
    for fam, w, fn in FACES
)

# OKOA tokens css — drop its broken relative @font-face rules (fonts are embedded above)
okoa = open("okoa-ridgeline.css").read()
okoa = re.sub(r"@font-face\{[^}]*\}", "", okoa)
layout = open("memo-layout.css").read()

html = open("memo.html").read()
for link in ("okoa-ridgeline.css", "memo-layout.css", "fonts.css"):
    html = re.sub(r'\s*<link rel="stylesheet" href="' + re.escape(link) + r'">', "", html)

style = (
    "<style>/* fonts (embedded) */\n" + font_css + "\n</style>\n"
    "<style>/* okoa tokens */\n" + okoa + "\n</style>\n"
    "<style>/* memo layout */\n" + layout + "\n</style>"
)
html = html.replace("</head>", style + "\n</head>", 1)

out = "zermatt-credit-memo.html"
open(out, "w").write(html)
print(f"wrote {out}  ({os.path.getsize(out)//1024} KB, self-contained)")
