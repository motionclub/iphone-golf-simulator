#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-tailoring";P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3;B=/Applications/Blender.app/Contents/MacOS/Blender;E=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
"$B" -b -t 2 --python "$W/scripts/pocket_lining.py" > "$W/logs/pocket_lining.log" 2>&1
if rg -q 'Traceback' "$W/logs/pocket_lining.log";then exit 1;fi
GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_Male_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- Male > "$W/logs/export_final_Male.log" 2>&1
if rg -q 'Traceback' "$W/logs/export_final_Male.log";then exit 1;fi
"$P" "$W/scripts/pack_golf_uv.py" Male Bottom > "$W/logs/pack_final_Male.log" 2>&1
"$P" "$W/scripts/repair_bottom_uv.py" > "$W/logs/repair_bottom_uv.log" 2>&1
for sex in Male Female; do
 "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_Bottom" > "$W/logs/bake_${sex}_Bottom.log" 2>&1
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_final_${sex}.log" 2>&1
 if rg -q 'Traceback' "$W/logs/apply_final_${sex}.log";then exit 1;fi
done
"$P" "$W/scripts/install_review.py"
GOLF_KIT_SOURCE="$W/export/kit_v2" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.GolfHeroKit.Build -logFile "$W/logs/rebuild_final.log"
TAILOR_OUT="$W/proof/final" MH_LOCKER_OUT="$W/native" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.TailoringProof.After -logFile "$W/logs/unity_final.log"
"$P" "$W/scripts/uv_check.py" > "$W/logs/uv_check.log" 2>&1
"$P" "$W/scripts/compress_maps.py" > "$W/logs/compress_maps.log" 2>&1
TAILOR_ASSETS="$W/native" "$W/native-render" "$W/proof/native" static > "$W/logs/native_render.log" 2>&1
