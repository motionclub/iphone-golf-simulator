#!/bin/bash
set -euo pipefail
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
cd "$R"
B="/Applications/Blender.app/Contents/MacOS/Blender"
W="work/golf-look"
for sex in Female Male; do
  "$B" -b "$W/export/Golf_${sex}_Draft.blend" --python "$W/scripts/fit_top_weights.py" -- "$sex" > "$W/logs/fit_${sex}_resume30b.log" 2>&1
  "$B" -b "$W/export/Golf_${sex}_Draft.blend" --python "$W/scripts/retarget_proof.py" -- "$sex" > "$W/logs/retarget_${sex}_resume30b.log" 2>&1
done
"$B" -b --python "$W/scripts/verify_identity.py" > "$W/logs/identity_resume30b.log" 2>&1
