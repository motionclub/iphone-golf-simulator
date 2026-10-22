#!/bin/bash
# usage: run_swaycheck.sh <label>   -> v2/sway/swaycheck_<label>.txt (GATE lines), logs/swaycheck_<label>.log, rig frames in v2/sway/rig_<label>/
# GolfPlantSwayCheck (shader compile, mirror vs GPU, wind, caps, real meshes) through heavy.sh (serialised with every other Unity / xcodebuild run).
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; L="$1"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p "$R/work/postcard-look/v2/sway/logs" "$R/work/postcard-look/v2/sway/rig_$L"
GOLF_SWAY_REPORT="$R/work/postcard-look/v2/sway/swaycheck_$L.txt" GOLF_SWAY_SHOTS="$R/work/postcard-look/v2/sway/rig_$L" \
  "$R/work/postcard-look/heavy.sh" "U-swaycheck-$L" "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.GolfPlantSwayCheck.Run \
  -logFile "$R/work/postcard-look/v2/sway/logs/swaycheck_$L.log"
rc=$?
echo "swaycheck $L exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v2/sway/logs/swaycheck_$L.log")"
exit $rc
