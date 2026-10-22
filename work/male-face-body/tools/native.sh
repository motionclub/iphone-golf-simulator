#!/bin/zsh
# Staging-only lobby parity for the female face pass: export (RunDistance) from ~/female-face-UnityClone (must hold the NEW state),
# overlay onto an APFS copy of CharacterAssets, Unity CaptureLobbyParity (tennis) vs the app's SceneKit code with OUR MatchHeroSurfaces.swift.
# <tag> = output folder name under native/. Nothing is installed into GolfArcade/.
set -e
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$REPO/work/male-face-body; OUT=$W/native/$1
U="$REPO/work/delegation-2026-10-17/heavy.sh unity /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity"; CLONE=$HOME/male-face-UnityClone; SWIFT=${2:-$W/unity/MatchHeroSurfaces.swift}
export GOLF_MUTE=1
rm -rf $OUT; mkdir -p $OUT/export $OUT/golden $OUT/logs $OUT/unity/tennis $OUT/lobby/tennis $OUT/sheets
MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$OUT/export MH_LOCKER_GOLDEN=$OUT/golden MH_LOCKER_REPORT=$OUT/logs/RunDistance-report.txt \
  $H unity env GOLF_MUTE=1 MH_LOCKER_FACE_PARITY=0 MH_LOCKER_OUT=$OUT/export MH_LOCKER_GOLDEN=$OUT/golden MH_LOCKER_REPORT=$OUT/logs/RunDistance-report.txt /Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity -batchmode -nographics -quit -projectPath $CLONE -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.RunDistance -logFile $OUT/logs/RunDistance.log
cp -cR $REPO/GolfArcade/Unity/CharacterAssets $OUT/assets
n=0; for f in $OUT/export/*.*; do if ! cmp -s $f $OUT/assets/${f:t}; then cp $f $OUT/assets/; n=$((n+1)); echo "  changed ${f:t}" >> $OUT/logs/changed.txt; fi; done; echo "export: $n changed files"
LP_OUT=$OUT/unity/tennis LP_GOLF=0 eval $U -batchmode -quit -projectPath $CLONE -executeMethod GolfArcade.EditorTools.MatchHeroLockerExport.CaptureLobbyParity -logFile $OUT/logs/capture.log
swiftc -swift-version 6 -O -parse-as-library $REPO/work/hero-sync/lobby_render.swift $REPO/GolfArcade/Unity/MatchHeroData.swift $SWIFT \
  $REPO/GolfArcade/Unity/MatchHeroMotion.swift -framework SceneKit -framework AppKit -framework Metal -o $OUT/lobby_render
LP_ASSETS=$OUT/assets LP_DISTANCE=1 $OUT/lobby_render $OUT/lobby/tennis 2>&1 | grep -v "^$" | grep -iv warning | tail -3 || true
python3 $REPO/work/hero-sync/compare.py $OUT $OUT/sheets 2>&1 | tail -5
echo NATIVE_DONE
