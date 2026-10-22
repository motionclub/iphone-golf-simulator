#!/bin/bash
# usage: tune_board.sh <label> <hole 8|9|10> '<HOLETINT string>' : GolfLookSmoke TUNE mode, one hole's grass board with in-memory tint overrides, on the clone, through heavy.sh -> v9/tune_<label>.txt
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v9
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
L="$1"; H="$2"; T="$3"; mkdir -p $V/logs $V/tune_shots_$L
env GOLF_LOOK_TUNE=1 GOLF_LOOK_GRASS_HOLE=$H GOLF_LOOK_HOLETINT="$T" GOLF_LOOK_SMOKE_REPORT=$V/tune_$L.txt GOLF_LOOK_SMOKE_SHOTS=$V/tune_shots_$L "$R/work/postcard-look/heavy.sh" "T9-tune-$L" "$U" -batchmode -projectPath "$SC/UnityClone" -executeMethod GolfArcade.EditorTools.GolfLookSmoke.Run -logFile $V/logs/tune_$L.log
grep "GRASS" $V/tune_$L.txt | cut -c1-420
