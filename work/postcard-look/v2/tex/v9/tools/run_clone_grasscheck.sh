#!/bin/bash
# usage: run_clone_grasscheck.sh <label> : GolfLookGrassCheck (creates the keeper material) on the clone, through heavy.sh
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; V=$R/work/postcard-look/v2/tex/v9
SC=/private/tmp/claude-501/-Users-adnanyonathan-Documents-Codex-2026-09-20-wh-outputs-iphone-golf-simulator/b67a5225-b7e5-4252-b92f-b4ee9f4f2d01/scratchpad
U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
L="$1"; mkdir -p $V/logs
env GOLF_GRASS_CREATE_KEEPER=1 GOLF_GRASS_CHECK_REPORT=$V/grasscheck_$L.txt "$R/work/postcard-look/heavy.sh" "T9-clone-gc-$L" "$U" -batchmode -projectPath "$SC/UnityClone" -executeMethod GolfArcade.EditorTools.GolfLookGrassCheck.Run -logFile "$V/logs/clone_grasscheck_$L.log"
echo "grasscheck $L exit $?; compile errors: $(grep -c 'error CS' $V/logs/clone_grasscheck_$L.log)"; cat $V/grasscheck_$L.txt 2>/dev/null
