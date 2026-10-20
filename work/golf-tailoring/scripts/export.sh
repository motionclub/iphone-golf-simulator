#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-tailoring"
B=/Applications/Blender.app/Contents/MacOS/Blender
P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
for sex in Male Female; do
 GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_${sex}_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- "$sex" > "$W/logs/export_${sex}.log" 2>&1
 if rg -q 'Traceback' "$W/logs/export_${sex}.log";then exit 1;fi
 for part in Top Bottom Shoe_L Shoe_R; do
  "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_${part}" > "$W/logs/bake_${sex}_${part}.log" 2>&1
 done
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_${sex}.log" 2>&1
 if rg -q 'Traceback' "$W/logs/apply_${sex}.log";then exit 1;fi
done
