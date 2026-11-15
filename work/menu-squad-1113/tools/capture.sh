#!/bin/bash
# capture.sh <label> [venue]: films the TV menu in the menu-squad clone (windowed, muted) into work/menu-squad-1113/shots/<label>
REPO=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$REPO/work/menu-squad-1113; P=$HOME/unity-clones/menu-squad/Unity
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
L=$1; V=${2:-tennis-resort}; OUT=$W/shots/$L; mkdir -p "$OUT"; rm -f "$OUT"/*
cp $W/tools/MenuSquadCapture.cs $P/Assets/Tests/PlayMode/
rm -f "$P/Temp/UnityLockfile"
env GOLF_MUTE=1 MENU_PROOF_DIR="$OUT/phone" MSQ_LIGHT=${MSQ_LIGHT:-0} MSQ_OUT="$OUT" MENU_BACKDROP="$V" $REPO/work/delegation-2026-10-17/heavy.sh unity $UNITY -projectPath "$P" -runTests -testPlatform PlayMode \
  -testFilter "${FILTER:-GolfArcade.Tests.MenuSquadCapture}" -testResults $W/logs/$L.xml -logFile $W/logs/$L.log
echo "rc=$? files=$(ls "$OUT" | wc -l)"
