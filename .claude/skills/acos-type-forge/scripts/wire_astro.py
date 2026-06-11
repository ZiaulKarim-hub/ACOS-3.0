#!/usr/bin/env python3
"""Wire a finished font into an Astro project that uses the native Fonts API.

Copies the font into <astro>/src/fonts/ and prints the exact `fonts:` entry to
add (or the line to swap) in astro.config.mjs, mapped to a CSS variable. Because
Astro pages reference the cssVariable token, swapping the provider makes the new
font appear everywhere with no page edits.

Config editing is left as a printed snippet on purpose — astro.config.mjs is live
JS and a blind regex patch can corrupt it. Paste the snippet (or replace the
matching `fontProviders.google()` block for the same cssVariable).

Usage:
  python3 wire_astro.py --font build/Foo-Regular.woff2 --astro /path/to/site \
      --css-var --font-titling --family "Foo"
"""
import argparse, os, shutil

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--astro", required=True, help="Astro project root")
    ap.add_argument("--css-var", required=True, help="e.g. --font-titling")
    ap.add_argument("--family", required=True)
    ap.add_argument("--weight", default="400")
    ap.add_argument("--style", default="normal")
    a = ap.parse_args()
    dest_dir = os.path.join(a.astro, "src", "fonts")
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.basename(a.font)
    shutil.copy(a.font, os.path.join(dest_dir, fname))
    rel = f"./src/fonts/{fname}"
    snippet = f'''    {{
      // {a.family} — local derivative; replaces the previous provider for {a.css_var}
      provider: "local",
      name: "{a.family}",
      cssVariable: "{a.css_var}",
      variants: [
        {{ weight: {a.weight}, style: "{a.style}", src: ["{rel}"] }},
      ],
    }},'''
    print(f"✓ copied {fname} -> {dest_dir}\n")
    print(f"In astro.config.mjs, inside `fonts: [ ... ]`, ADD this entry (or REPLACE")
    print(f"the existing fontProviders.google() block whose cssVariable is {a.css_var}):\n")
    print(snippet)
    print(f"\nThen every element using var({a.css_var}) renders in {a.family}. Restart `astro dev`.")

if __name__ == "__main__":
    main()
