#!/bin/bash
# usage: run_clone_stills.sh <label> <outdir-abs> <cfg-abs> [extra env VAR=val ...] : PostcardLookStills on the APFS CLONE of the Unity project (scratchpad), through heavy.sh
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
L="$1"; O="$2"; CFG="$3"; shift; shift; shift; mkdir -p "$O"
LOG="$R/work/postcard-look/v2/tex/v9/logs/clone_stills_$L.log"; mkdir -p "$(dirname "$LOG")"
env "$@" GOLF_STILLS_OUT="$O" GOLF_STILLS_CFG="$CFG" "$R/work/postcard-look/heavy.sh" "T9-clone-$L" "$U" -batchmode -projectPath "$SC/UnityClone" -executeMethod GolfArcade.EditorTools.PostcardLookStills.Run -logFile "$LOG"
echo "clone stills $L exit $?; compile errors: $(grep -c 'error CS' "$LOG"); shots: $(grep -c '^\[PostcardLookStills\] hole' "$LOG")"
