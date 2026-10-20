#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-tailoring";P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3;B=/Applications/Blender.app/Contents/MacOS/Blender;E=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
"$B" -b -t 2 --python "$W/scripts/waist_stable_hip.py" > "$W/logs/waist_stable_hip.log" 2>&1
if rg -q 'Traceback' "$W/logs/waist_underlap.log";then exit 1;fi
GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_Male_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- Male > "$W/logs/export_last_Male.log" 2>&1
if rg -q 'Traceback' "$W/logs/export_last_Male.log";then exit 1;fi
"$B" -b "$W/export/kit_v2/Golf_Male_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- Male > "$W/logs/apply_last_Male.log" 2>&1
"$P" "$W/scripts/install_review.py"
GOLF_KIT_SOURCE="$W/export/kit_v2" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.GolfHeroKit.Build -logFile "$W/logs/rebuild_last.log"
TAILOR_OUT="$W/proof/verified" MH_LOCKER_OUT="$W/native" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.TailoringProof.After -logFile "$W/logs/unity_verified.log"
"$P" "$W/scripts/uv_check.py" > "$W/logs/uv_check.log" 2>&1
"$P" "$W/scripts/compress_maps.py" > "$W/logs/compress_maps.log" 2>&1
TAILOR_ASSETS="$W/native" "$W/native-render" "$W/proof/native_verified" static > "$W/logs/native_verified.log" 2>&1
"$P" "$W/scripts/check_assets.py" > "$W/logs/final_assets.log" 2>&1
