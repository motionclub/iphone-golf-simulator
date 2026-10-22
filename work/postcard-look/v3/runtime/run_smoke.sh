#!/bin/bash
# usage: run_smoke.sh <label> [extra env assignments...]   e.g. run_smoke.sh s1 GOLF_LOOK_SWEEP=1
# Runs GolfLookSmoke through heavy.sh (serialised with every other Unity / xcodebuild run) and writes
# v2/runtime/smoke_<label>.txt (GATE lines), logs/smoke_<label>.log, shots/<label>/*.jpg. Exit code = Unity's (1 = a gate failed).
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; L="$1"; shift
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p "$R/work/postcard-look/v3/runtime/logs" "$R/work/postcard-look/v3/runtime/shots/$L"
env "$@" GOLF_LOOK_SMOKE_REPORT="$R/work/postcard-look/v3/runtime/smoke_$L.txt" GOLF_LOOK_SMOKE_SHOTS="$R/work/postcard-look/v3/runtime/shots/$L" \
  "$R/work/postcard-look/heavy.sh" "R-smoke-$L" "$U" -batchmode -projectPath "$R/Unity" -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run \
  -logFile "$R/work/postcard-look/v3/runtime/logs/smoke_$L.log"
rc=$?
echo "smoke $L exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v3/runtime/logs/smoke_$L.log")"
exit $rc
