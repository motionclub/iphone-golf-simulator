#!/bin/bash
# tools/capture.sh <out_dir>  — every player view per golf hole (MajesticHoleViews), muted, in ~/majestic-all-maps-UnityClone.
# env: MAM_HOLES (default all 16), DREAM_WEATHER (Clear), DREAM_UTC, MAM_FRESH=1 re-clones Unity/.
# Always launched through work/delegation-2026-10-17/heavy.sh (1 Unity machine-wide).
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/majestic-all-maps-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
if [ ! -d "$CLONE" ] || [ "${MAM_FRESH:-0}" = 1 ]; then rm -rf "$CLONE"; cp -cR "$ROOT/Unity" "$CLONE"; rm -rf "$CLONE/Temp"; fi
mkdir -p "$CLONE/Assets/Editor"
cp "$ROOT/work/majestic-all-maps/unity/Assets/Editor/MajesticHoleViews.cs" "$CLONE/Assets/Editor/"
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 MAM_OUT=$OUT "$ROOT/work/delegation-2026-10-17/heavy.sh" unity "$UNITY" -projectPath "$CLONE" -executeMethod GolfArcade.EditorTools.MajesticHoleViews.Run -logFile "$OUT/unity.log" &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if grep -q "Scripts have compiler errors\|error CS" "$OUT/unity.log" 2>/dev/null; then grep "error CS" "$OUT/unity.log" | sort -u | head -8; pkill -f "projectPath $CLONE"; break; fi
  sleep 5
done
wait $PID; rc=$?; grep -E "error CS|\[MajesticHoleViews\]|Exception" "$OUT/unity.log" | sort -u | head -40; echo "rc=$rc -> $OUT"
