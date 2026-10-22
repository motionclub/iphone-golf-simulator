#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
U="$W/isolation/PostClothUnity"
E=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
bash work/postcard-look/heavy.sh golf_copy_r36 /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 "$W/scripts/import_locked_r36.py"
bash work/postcard-look/heavy.sh golf_import_r36 env GOLF_KIT_SOURCE="$W/export/kit_v2" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.GolfHeroKit.Build -logFile "$W/logs/unity_import_r36.log"
bash work/postcard-look/heavy.sh golf_course_r36 env GOLF_MESH_DUMP="$W/data/runtime_skin_r36" GOLF_SURFACE_AUDIT=1 GOLF_V3_PROOF_CFG="$W/data/ground_audit_cfg_r36.json" GOLF_LOOK_OUT="$W/proof/course_kit_final_r36" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.GolfLookProofRig.Run -logFile "$W/logs/unity_course_r36.log"
bash work/postcard-look/heavy.sh golf_locker_export_r36 env MH_LOCKER_OUT="$W/locker/assets" MH_LOCKER_REPORT="$W/data/locker_export_r36.txt" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.RunGolf -logFile "$W/logs/unity_locker_export_r36.log"
