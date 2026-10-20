#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-tailoring";P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3;B=/Applications/Blender.app/Contents/MacOS/Blender
for sex in Male Female; do
 "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_Bottom" > "$W/logs/bake_${sex}_Bottom.log" 2>&1
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/apply_${sex}.log" 2>&1
 if rg -q 'Traceback' "$W/logs/apply_${sex}.log";then exit 1;fi
done
"$P" "$W/scripts/install_review.py"
TAILOR_OUT="$W/proof/after" MH_LOCKER_OUT="$W/native" /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.TailoringProof.After -logFile "$W/logs/unity_after.log"
