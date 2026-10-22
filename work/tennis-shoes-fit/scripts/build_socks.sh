#!/bin/bash
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit
B=/Applications/Blender.app/Contents/MacOS/Blender
for g in ${@:-male female}; do
  $B -b --factory-startup --python scripts/sock.py -- $g 2>&1 | grep -E "Error|Trace|WARNING|sock\[|split|File \"|SDF|AssertionError" | cut -c1-300
done
