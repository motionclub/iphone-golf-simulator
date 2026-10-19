#!/bin/bash
# Golf proof captures in the rendered-backgrounds clone.
#   tools/capture_golf.sh <out_dir> [holes=7,13,10] [utc] [weather]
# Env passthrough: BG_PERF_AB=1, RENDERED_SKY=0 (before), RENDERED_BG_VENUES.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=${BG_CLONE:-/private/tmp/backgrounds-UnityClone}
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd); HOLES=${2:-7,13,10}; UTC=${3:-1792263600}; WEATHER=${4:-Clear}
LOG=$ROOT/work/rendered-backgrounds/logs/golf_$(basename "$OUT").log
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 BG_OUT=$OUT BG_HOLES=$HOLES DREAM_UTC=$UTC DREAM_WEATHER=$WEATHER "$UNITY" -batchmode -projectPath "$CLONE" \
  -executeMethod GolfArcade.EditorTools.RenderedBackgroundsGolfCapture.Run -logFile "$LOG"
rc=$?
grep -E "error CS|\[BgGolfCapture\]|Exception" "$LOG" | sort -u | head -20
echo "rc=$rc -> $OUT"
