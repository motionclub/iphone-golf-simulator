#!/bin/bash
# Venue proof capture: compile-only pass (-nographics), then one graphics capture per venue.
#   work/venue-presence/tools/capture.sh <out_dir> <venue> [venue ...]     venue = skyscraper | volcano | resort
# Env passed through: HERO_VENUE_DUMP=1 (kit + triangle dump), HERO_VENUE_DUMP_KIT=1 (per-renderer kit lines).
# Never writes to ArtDir: HERO_VENUE_OUT is always set to <out_dir>.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(cd "$(dirname "$1")" 2>/dev/null && pwd)/$(basename "$1"); shift
LOGS=$ROOT/work/venue-presence/logs
mkdir -p "$OUT" "$LOGS"

if pgrep -f "Unity.app/Contents/MacOS/Unity -" >/dev/null 2>&1 || [ -e "$ROOT/Unity/Temp/UnityLockfile" ]; then
  if pgrep -f "Unity.app/Contents/MacOS/Unity" | xargs -I{} ps -o command= -p {} 2>/dev/null | grep -q "$ROOT/Unity"; then
    echo "Unity already has this project open; aborting" >&2; exit 2
  fi
fi

echo "== compile pass"
"$UNITY" -batchmode -nographics -quit -projectPath "$ROOT/Unity" -logFile "$LOGS/compile.log"
rc=$?
if grep -q "error CS" "$LOGS/compile.log"; then echo "COMPILE ERRORS:"; grep "error CS" "$LOGS/compile.log" | sort -u | head -30; exit 3; fi
echo "compile pass rc=$rc"

for v in "$@"; do
  echo "== capture $v -> $OUT"
  HERO_VENUE=$v HERO_VENUE_OUT=$OUT "$UNITY" -batchmode -projectPath "$ROOT/Unity" \
    -executeMethod GolfArcade.EditorTools.TennisVenueCapture.Run -logFile "$LOGS/capture_$v.log"
  echo "capture $v rc=$?"
  grep -E "VenueCapture|VenueDump|Exception|error CS" "$LOGS/capture_$v.log" | head -40
done
echo "== done"
