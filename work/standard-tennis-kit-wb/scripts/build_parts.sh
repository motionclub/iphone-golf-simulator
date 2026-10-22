#!/bin/bash
# rebuild all garment parts (npz in data/).  usage: build_parts.sh [parts...]  default: all
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb
B=/Applications/Blender.app/Contents/MacOS/Blender
run() { $B -b --factory-startup --python "$@" 2>&1 | grep -E "Error|Trace|total|sock\[|shoe\[|File \"" ; }
PARTS=${@:-"polo_m polo_f shorts skort sock_m sock_f sock_fa shoe_m shoe_f shoe_fa"}
for p in $PARTS; do
  case $p in
    polo_m) run scripts/polo.py -- male white ;;
    polo_f) run scripts/polo.py -- female white ;;
    shorts) run scripts/shorts.py ;;
    skort) run scripts/skort.py ;;
    sock_m) run scripts/sock.py -- male ;;
    sock_f) run scripts/sock.py -- female ;;
    shoe_m) run scripts/shoe.py -- male ;;
    shoe_f) run scripts/shoe.py -- female ;;
    sock_fa) run scripts/sock.py -- female_auth ;;
    shoe_fa) run scripts/shoe.py -- female_auth ;;
  esac
done
