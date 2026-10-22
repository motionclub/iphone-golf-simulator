#!/bin/bash
# Plaza hub proof (PlayMode test RenderedBackgroundsHubProof) in the rendered-backgrounds clone, windowed, muted.
#   tools/capture_hub.sh <out_dir>      env: RENDERED_BG_VENUES (add hub for the after run), BG_PERF_AB=1
set -u
CLONE=${BG_CLONE:-/private/tmp/backgrounds-UnityClone}
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 BG_OUT=$OUT "$UNITY" -projectPath "$CLONE" -runTests -testPlatform PlayMode \
  -testFilter GolfArcade.Tests.RenderedBackgroundsHubProof.Plaza -testResults "$OUT/results.xml" -logFile "$OUT/unity.log"
grep -o 'result="[A-Za-z]*"' "$OUT/results.xml" | head -2; grep -E "error CS|Exception" "$OUT/unity.log" | sort -u | head -5
echo "-> $OUT"
