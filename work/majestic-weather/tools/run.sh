#!/bin/bash
# tools/run.sh <out_dir> — one muted, windowed Unity run of MajesticWeatherShots in ~/majestic-weather-UnityClone,
# through heavy.sh (1 Unity machine-wide). Env passes through: MW_SLOTS, MW_JOBS, MW_ROUNDS, MW_SAMPLES, MW_VIDEO_SECONDS.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/majestic-weather-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
bash "$ROOT/work/majestic-weather/tools/sync.sh"
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 MW_OUT=$OUT MW_ORIG_DIR=$ROOT/work/majestic-weather/proof/orig \
  "$ROOT/work/delegation-2026-10-17/heavy.sh" unity "$UNITY" -projectPath "$CLONE" -executeMethod GolfArcade.EditorTools.MajesticWeatherShots.Run -logFile "$OUT/unity.log" &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if grep -q "Scripts have compiler errors\|error CS" "$OUT/unity.log" 2>/dev/null; then grep "error CS" "$OUT/unity.log" | sort -u | head -8; pkill -f "projectPath $CLONE"; break; fi
  sleep 5
done
wait $PID; rc=$?
grep -E "error CS|\[MajesticWeather\]|Exception|Shader error|shader.*error" "$OUT/unity.log" | sort -u | head -80; echo "rc=$rc -> $OUT"
