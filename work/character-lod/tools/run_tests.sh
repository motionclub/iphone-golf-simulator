#!/bin/bash
# tools/run_tests.sh <out_dir> — CharacterLodTests (EditMode, batch) in ~/character-lod-UnityClone through heavy.sh.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/character-lod-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
rsync -a "$ROOT/work/character-lod/src/" "$CLONE/Assets/Scripts/CharacterLod/"
rsync -a "$ROOT/work/character-lod/unity/Assets/Tests/" "$CLONE/Assets/Tests/"
GOLF_MUTE=1 "$ROOT/work/delegation-2026-10-17/heavy.sh" unity "$UNITY" -batchmode -projectPath "$CLONE" -runTests -testPlatform EditMode \
  -testFilter "${CLOD_TESTS:-GolfArcade.Tests.CharacterLodTests}" -testResults "$OUT/tests.xml" -logFile "$OUT/tests.log"
rc=$?; grep -oE 'total="[0-9]+" passed="[0-9]+" failed="[0-9]+"' "$OUT/tests.xml" 2>/dev/null; echo "rc=$rc"
