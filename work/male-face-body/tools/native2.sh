#!/bin/zsh
# continue native parity after the export step: tools/native2.sh <tag>  (export already in native/<tag>/export)
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/male-face-body; OUT=$W/native/$1
H=$REPO/work/delegation-2026-10-17/heavy.sh; U=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity; CLONE=$HOME/male-face-UnityClone; SWIFT=$W/unity/MatchHeroSurfaces.swift
rm -rf $OUT/assets; cp -cR $REPO/GolfArcade/Unity/CharacterAssets $OUT/assets
n=0; for f in $OUT/export/*.*; do if ! cmp -s $f $OUT/assets/${f:t}; then cp $f $OUT/assets/; n=$((n+1)); echo "  changed ${f:t}" >> $OUT/logs/changed.txt; fi; done; echo "export: $n changed files"
$H unity env GOLF_MUTE=1 LP_OUT=$OUT/unity/tennis LP_GOLF=0 $U -batchmode -quit -projectPath $CLONE -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.CaptureLobbyParity -logFile $OUT/logs/capture.log
swiftc -swift-version 6 -O -parse-as-library $REPO/work/hero-sync/lobby_render.swift $REPO/GolfArcade/Unity/MatchHeroData.swift $SWIFT \
  $REPO/GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal -o $OUT/lobby_render
LP_ASSETS=$OUT/assets LP_DISTANCE=1 $OUT/lobby_render $OUT/lobby/tennis 2>&1 | grep -v "^$" | grep -iv warning | tail -3 || true
python3 $REPO/work/hero-sync/compare.py $OUT $OUT/sheets 2>&1 | tail -5
echo NATIVE_DONE
