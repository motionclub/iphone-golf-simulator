#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
B=/Applications/Blender.app/Contents/MacOS/Blender
P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
for sex in Male Female; do
 GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_${sex}_SwingProof.blend" --python "$W/scripts/export_golf_kit.py" -- "$sex" > "$W/logs/export_lineage_${sex}_r23.log" 2>&1
done
"$P" "$W/scripts/pack_golf_uv.py" Male Top > "$W/logs/pack_Male_Top_r23.log" 2>&1
"$P" "$W/scripts/pack_golf_uv.py" Female Top > "$W/logs/pack_Female_Top_r23.log" 2>&1
"$P" "$W/scripts/pack_golf_uv.py" Male Bottom > "$W/logs/pack_Male_Bottom_r23.log" 2>&1
"$P" "$W/scripts/repair_uv_slivers.py" > "$W/logs/uv_slivers_r23.log" 2>&1
for piece in Male_Kit_Top Female_Kit_Top Male_Kit_Bottom; do
 "$P" "$W/scripts/bake_golf_maps.py" "$piece" > "$W/logs/bake_${piece}_r23.log" 2>&1
done
for sex in Male Female; do
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_uv_${sex}_r23.log" 2>&1
done
"$P" "$W/scripts/prepare_locker_maps.py" > "$W/logs/locker_maps_r23.log" 2>&1
