#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
B=/Applications/Blender.app/Contents/MacOS/Blender
P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
for sex in Male Female; do
 GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_${sex}_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- "$sex" > "$W/logs/export_placket_${sex}_r36.log" 2>&1
 if rg -q 'Traceback' "$W/logs/export_placket_${sex}_r36.log";then exit 1;fi
 "$P" "$W/scripts/pack_golf_uv.py" "$sex" Top > "$W/logs/pack_placket_${sex}_r36.log" 2>&1
done
"$P" "$W/scripts/repair_uv_slivers.py" > "$W/logs/uv_slivers_r36.log" 2>&1
for sex in Male Female; do
 "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_Top" > "$W/logs/bake_placket_${sex}_r36.log" 2>&1
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_uv_${sex}_r36.log" 2>&1
 if rg -q 'Traceback' "$W/logs/apply_uv_${sex}_r36.log";then exit 1;fi
done
"$P" "$W/scripts/prepare_locker_maps.py" > "$W/logs/locker_maps_r36.log" 2>&1
