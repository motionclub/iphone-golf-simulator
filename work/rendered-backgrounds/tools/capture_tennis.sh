#!/bin/bash
# Tennis venue proof captures in the rendered-backgrounds clone.
#   tools/capture_tennis.sh <out_dir> <venue> [utc] [weather]
#   venue = resort|skyscraper|volcano; utc default 1792263600 (14:00 EST, clear day); weather default Clear
# Env passthrough: BG_SHOTS=a,b (only those shots), BG_PERF=1 (perf proxy).
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=${BG_CLONE:-/private/tmp/backgrounds-UnityClone}
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd); VENUE=$2; UTC=${3:-1792263600}; WEATHER=${4:-Clear}
LOG=$ROOT/work/rendered-backgrounds/logs/capture_${VENUE}_$(basename "$OUT").log
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 HERO_VENUE=$VENUE BG_OUT=$OUT DREAM_UTC=$UTC DREAM_WEATHER=$WEATHER "$UNITY" -batchmode -projectPath "$CLONE" \
  -executeMethod GolfArcade.EditorTools.RenderedBackgroundsCapture.Run -logFile "$LOG"
rc=$?
grep -E "error CS|\[BgCapture\]" "$LOG" | sort -u | head -20
echo "rc=$rc -> $OUT"
