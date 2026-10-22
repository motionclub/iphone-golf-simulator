#!/bin/bash
set -euo pipefail
W="$PWD/work/golf-look"
U="$W/isolation/PostClothUnity"
E=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
bash work/postcard-look/heavy.sh golf_import_r24 env GOLF_KIT_SOURCE="$W/export/kit_v2" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.GolfHeroKit.Build -logFile "$W/logs/unity_import_r24.log"
bash work/postcard-look/heavy.sh golf_course_final_r24 env GOLF_LOOK_OUT="$W/proof/course_kit_final_r24" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.GolfLookProofRig.Run -logFile "$W/logs/unity_course_final_r24.log"
bash work/postcard-look/heavy.sh golf_locker_export_r24 env MH_LOCKER_OUT="$W/locker/assets" MH_LOCKER_REPORT="$W/data/locker_export_r24.json" "$E" -batchmode -projectPath "$U" -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.RunGolf -logFile "$W/logs/unity_locker_export_r24.log"
