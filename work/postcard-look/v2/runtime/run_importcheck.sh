#!/bin/bash
# usage: run_importcheck.sh <label>   -> v2/runtime/importcheck_<label>.txt, logs/importcheck_<label>.log
R="$(cd "$(dirname "$0")/../../../.." && pwd)"; L="$1"
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
POSTCARD_IMPORT_REPORT="$R/work/postcard-look/v2/runtime/importcheck_$L.txt" "$R/work/postcard-look/heavy.sh" "R-importcheck-$L" "$U" -batchmode -projectPath "$R/Unity" \
  -executeMethod GolfArcade.EditorTools.PostcardImportCheck.Run -logFile "$R/work/postcard-look/v2/runtime/logs/importcheck_$L.log"
rc=$?
echo "importcheck $L exit $rc; compile errors: $(grep -c 'error CS' "$R/work/postcard-look/v2/runtime/logs/importcheck_$L.log")"
exit $rc
