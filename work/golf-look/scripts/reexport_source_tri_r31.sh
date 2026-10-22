#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
B=/Applications/Blender.app/Contents/MacOS/Blender
P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_Female_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- Female > "$W/logs/export_source_tri_Female_r31.log" 2>&1
if rg -q 'Traceback' "$W/logs/export_source_tri_Female_r31.log"; then exit 1; fi
"$P" "$W/scripts/pack_golf_uv.py" > "$W/logs/pack_source_tri_r31.log" 2>&1
"$P" "$W/scripts/repair_uv_slivers.py" > "$W/logs/uv_slivers_r31.log" 2>&1
"$P" "$W/scripts/bake_golf_maps.py" > "$W/logs/bake_source_tri_r31.log" 2>&1
for sex in Male Female; do
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_uv_${sex}_r31.log" 2>&1
 if rg -q 'Traceback' "$W/logs/apply_uv_${sex}_r31.log"; then exit 1; fi
done
"$P" "$W/scripts/prepare_locker_maps.py" > "$W/logs/locker_maps_r31.log" 2>&1
