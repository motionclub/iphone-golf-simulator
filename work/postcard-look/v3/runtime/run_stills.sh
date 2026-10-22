#!/bin/bash
# usage: run_stills.sh <label> <outdir> [env assignments...]   e.g. run_stills.sh t1 work/postcard-look/v3/runtime/stills_test GOLF_STILLS_CFG=...
# PostcardLookStills through heavy.sh. NEVER point <outdir> at ArtDir/screenshots/golf_postcards/look/ for a test.
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; L="$1"; O="$2"; shift; shift
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
mkdir -p "$R/work/postcard-look/v3/runtime/logs"
env "$@" GOLF_STILLS_OUT="$R/$O" "$R/work/postcard-look/heavy.sh" "R-stills-$L" "$U" -batchmode -projectPath "$R/Unity" \
  -executeMethod GolfArcade.EditorTools.PostcardLookStills.Run -logFile "$R/work/postcard-look/v3/runtime/logs/stills_$L.log"
rc=$?
echo "stills $L exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v3/runtime/logs/stills_$L.log"); shots: $(grep -c '^\[PostcardLookStills\] hole' "$R/work/postcard-look/v3/runtime/logs/stills_$L.log")"
exit $rc
