#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
B=/Applications/Blender.app/Contents/MacOS/Blender
P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
mkdir -p "$W/rollback/pocket_export_r24"
cp -R "$W/export/kit_v2" "$W/rollback/pocket_export_r24/kit_v2"
GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_Male_SwingProof.blend" --python "$W/scripts/export_golf_kit.py" -- Male > "$W/logs/export_pockets_Male_r24.log" 2>&1
"$P" "$W/scripts/pack_golf_uv.py" Male Bottom > "$W/logs/pack_pockets_Bottom_r24.log" 2>&1
"$P" "$W/scripts/bake_golf_maps.py" Male_Kit_Bottom > "$W/logs/bake_pockets_Bottom_r24.log" 2>&1
"$B" -b "$W/export/kit_v2/Golf_Male_KitUV.blend" --python "$W/scripts/apply_golf_uv.py" -- Male > "$W/logs/apply_pockets_Male_r24.log" 2>&1
"$P" "$W/scripts/prepare_locker_maps.py" > "$W/logs/locker_maps_r24.log" 2>&1
