#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-tailoring";P=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3;B=/Applications/Blender.app/Contents/MacOS/Blender;E=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
"$B" -b -t 2 --python "$W/scripts/refine_bottoms_followthrough.py" > "$W/logs/refine_bottoms_followthrough.log" 2>&1
if rg -q 'Traceback' "$W/logs/refine_bottoms_followthrough.log";then exit 1;fi
for sex in Male Female; do
 GOLF_REUSE_UV=1 "$B" -b "$W/export/Golf_${sex}_Draft.blend" -t 2 --python "$W/scripts/export_golf_kit.py" -- "$sex" > "$W/logs/follow_export_$sex.log" 2>&1
 if rg -q 'Traceback' "$W/logs/follow_export_$sex.log";then exit 1;fi
 "$P" "$W/scripts/pack_golf_uv.py" "$sex" Bottom > "$W/logs/follow_pack_$sex.log" 2>&1
 "$P" "$W/scripts/pack_golf_uv.py" "$sex" Top > "$W/logs/follow_pack_top_$sex.log" 2>&1
done
"$P" "$W/scripts/repair_bottom_uv.py" > "$W/logs/follow_repair_uv.log" 2>&1
"$P" "$W/scripts/repair_top_uv.py" > "$W/logs/follow_repair_top_uv.log" 2>&1
for sex in Male Female; do
 "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_Top" > "$W/logs/follow_bake_top_$sex.log" 2>&1
 "$P" "$W/scripts/bake_golf_maps.py" "${sex}_Kit_Bottom" > "$W/logs/follow_bake_$sex.log" 2>&1
 "$B" -b "$W/export/kit_v2/Golf_${sex}_KitUV.blend" -t 2 --python "$W/scripts/apply_golf_uv.py" -- "$sex" > "$W/logs/follow_apply_$sex.log" 2>&1
done
"$P" "$W/scripts/install_review.py"
GOLF_KIT_SOURCE="$W/export/kit_v2" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.GolfHeroKit.Build -logFile "$W/logs/follow_build.log"
TAILOR_OUT="$W/proof/followthrough/stills" MH_LOCKER_OUT="$W/native" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.TailoringProof.After -logFile "$W/logs/follow_stills.log"
SWING_OUT="$W/proof/followthrough/swing" "$E" -batchmode -job-worker-count 1 --burst-disable-compilation -projectPath "$W/Unity" -executeMethod GolfArcade.EditorTools.TailoringSwingPreview.Run -logFile "$W/logs/follow_swing.log"
"$P" "$W/scripts/uv_check.py" > "$W/logs/follow_uv_check.log" 2>&1
"$P" "$W/scripts/compress_maps.py" > "$W/logs/follow_compress.log" 2>&1
TAILOR_ASSETS="$W/native" "$W/native-render" "$W/proof/followthrough/native" static > "$W/logs/follow_native.log" 2>&1
"$P" "$W/scripts/check_assets.py" > "$W/logs/follow_assets.log" 2>&1
