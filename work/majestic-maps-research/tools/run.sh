#!/bin/bash
# Research-only: measure in the private clone. tools/run.sh <out_dir> ; env MAJ_* passed through (see MajesticCost.cs).
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=/private/tmp/majestic-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
cp "$ROOT/work/majestic-maps-research/tools/MajesticCost.cs" "$CLONE/Assets/Editor/MajesticCost.cs"
# frame timing stats on (clone only) so FrameTimingManager reports GPU time
sed -i '' 's/enableFrameTimingStats: 0/enableFrameTimingStats: 1/' "$CLONE/ProjectSettings/ProjectSettings.asset"
LOG=$OUT/unity.log
GOLF_MUTE=1 MAJ_OUT=$OUT "$UNITY" -projectPath "$CLONE" -executeMethod GolfArcade.EditorTools.MajesticCost.Run -logFile "$LOG"
rc=$?
grep -E "error CS|\[Majestic\]" "$LOG" | sort -u | head -60
echo "rc=$rc -> $OUT"
