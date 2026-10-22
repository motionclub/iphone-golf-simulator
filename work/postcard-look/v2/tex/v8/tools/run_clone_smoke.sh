#!/bin/bash
# usage: run_clone_smoke.sh <label> : GolfLookSmoke on the APFS CLONE of the Unity project (scratchpad), through heavy.sh -> v8/clone_smoke_<label>.txt / .log
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
L="$1"; D=$R/work/postcard-look/v2/tex/v8; mkdir -p $D/clone_smoke_shots_$L
env GOLF_LOOK_SMOKE_REPORT="$D/clone_smoke_$L.txt" GOLF_LOOK_SMOKE_SHOTS="$D/clone_smoke_shots_$L" "$R/work/postcard-look/heavy.sh" "T-clone-smoke-$L" "$U" -batchmode -projectPath "$SC/UnityClone" -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run -logFile "$D/clone_smoke_$L.log"
echo "clone smoke $L exit $?; compile errors: $(grep -c 'error CS' "$D/clone_smoke_$L.log")"
