#!/bin/bash
cd "/Users/zee/Documents/Vibe Coding/ACOS 3.0/Zermatt Credit Memo" || exit 1
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL="file://$PWD/memo.html"

run_to () {  # timeout_seconds cmd...
  local t=$1; shift
  "$@" & local pid=$!
  ( sleep "$t"; kill -9 "$pid" 2>/dev/null ) & local killer=$!
  wait "$pid" 2>/dev/null
  kill -9 "$killer" 2>/dev/null
}

shoot () {  # width height outfile
  local udd; udd="/tmp/okoachrome-$RANDOM$RANDOM"
  rm -f "$3"
  run_to 40 "$CHROME" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --user-data-dir="$udd" --force-device-scale-factor=1.4 \
    --window-size="$1,$2" --screenshot="$3" "$URL"
  rm -rf "$udd"
  if [ -f "$3" ]; then echo "OK   $3 ($(( $(stat -f%z "$3") / 1024 )) KB)"; else echo "FAIL $3"; fi
}

echo "== screenshots =="
shoot 1280 1780 shot-desktop.png
shoot 1024 1500 shot-tablet-land.png
shoot 768 1540 shot-tablet-port.png
shoot 390 1700 shot-mobile.png

echo "== pdf =="
udd="/tmp/okoachrome-pdf-$RANDOM$RANDOM"
rm -f "Zermatt-Credit-Memo.pdf"
run_to 70 "$CHROME" --headless=new --disable-gpu --no-sandbox --user-data-dir="$udd" \
  --no-pdf-header-footer --print-to-pdf="Zermatt-Credit-Memo.pdf" "$URL"
rm -rf "$udd"
if [ -f "Zermatt-Credit-Memo.pdf" ]; then echo "OK   PDF ($(( $(stat -f%z Zermatt-Credit-Memo.pdf) / 1024 )) KB)"; else echo "FAIL PDF"; fi

echo "== ALL-DONE =="
