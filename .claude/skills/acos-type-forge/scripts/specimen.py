#!/usr/bin/env python3
"""Render a before/after specimen PNG (PIL) comparing base vs derived font.

Usage:
  python3 specimen.py --base base.ttf --new build/Foo-Regular.ttf \
      --text "Type" --label "tracking + stencil cut" --out specimens/proof.png
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--text", default="Type")
    ap.add_argument("--label", default="modified")
    ap.add_argument("--out", default="specimen.png")
    ap.add_argument("--size", type=int, default=150)
    a = ap.parse_args()
    PAPER=(244,236,224); INK=(42,38,32); GILT=(178,119,74); FAINT=(150,138,120)
    W,H=1500,560
    img=Image.new("RGB",(W,H),PAPER); d=ImageDraw.Draw(img)
    base=ImageFont.truetype(a.base,a.size); new=ImageFont.truetype(a.new,a.size)
    lab=ImageFont.truetype(a.base,24)
    def center(text,font,y,fill):
        bb=d.textbbox((0,0),text,font=font); d.text(((W-(bb[2]-bb[0]))/2-bb[0],y),text,font=font,fill=fill)
    d.text((60,40),"BEFORE  ·  base font",font=lab,fill=FAINT); center(a.text,base,110,INK)
    d.line((60,300,W-60,300),fill=(0,0,0,30),width=1)
    d.text((60,330),f"AFTER  ·  {a.label}",font=lab,fill=GILT); center(a.text,new,400,INK)
    os.makedirs(os.path.dirname(a.out) or ".",exist_ok=True)
    img.save(a.out); print("wrote",a.out)

if __name__ == "__main__":
    main()
