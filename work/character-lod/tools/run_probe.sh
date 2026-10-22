#!/bin/bash
# tools/run_probe.sh <out_dir> — CharacterLodProbe in ~/character-lod-UnityClone, windowed + muted, through heavy.sh.
# Copies the runtime scripts (src/ -> Assets/Scripts/CharacterLod/) and the probe (unity/Assets/Editor) into the clone first.
# CLOD_FRESH=1 re-clones Unity/. Extra env (CLOD_HOLES, CLOD_STEPS, CLOD_CAMS) passes through.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/character-lod-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
if [ ! -d "$CLONE" ] || [ "${CLOD_FRESH:-0}" = 1 ]; then rm -rf "$CLONE"; cp -cR "$ROOT/Unity" "$CLONE"; rm -rf "$CLONE/Temp"; fi
mkdir -p "$CLONE/Assets/Scripts/CharacterLod" "$CLONE/Assets/Editor"
rsync -a "$ROOT/work/character-lod/src/" "$CLONE/Assets/Scripts/CharacterLod/"
rsync -a "$ROOT/work/character-lod/unity/Assets/Editor/" "$CLONE/Assets/Editor/"; rsync -a "$ROOT/work/character-lod/unity/Assets/Tests/" "$CLONE/Assets/Tests/"
[ -f "$ROOT/work/character-lod/install/HeroLodCache.bytes" ] && mkdir -p "$CLONE/Assets/Resources/CharacterLOD" && cp "$ROOT/work/character-lod/install/HeroLodCache.bytes" "$CLONE/Assets/Resources/CharacterLOD/"
export CLOD_CAMS=${CLOD_CAMS:-$ROOT/work/majestic-all-maps/audit/views_clear}
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 CLOD_OUT=$OUT "$ROOT/work/delegation-2026-10-17/heavy.sh" unity "$UNITY" -projectPath "$CLONE" -executeMethod GolfArcade.EditorTools.${CLOD_METHOD:-CharacterLodProbe}.Run -logFile "$OUT/unity.log" &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if grep -q "Scripts have compiler errors\|error CS" "$OUT/unity.log" 2>/dev/null; then grep "error CS" "$OUT/unity.log" | sort -u | head -8; pkill -f "projectPath $CLONE"; break; fi
  sleep 5
done
wait $PID; rc=$?; grep -E "error CS|\[CharacterLod\]|\[HeroLod\]|Exception" "$OUT/unity.log" | sort -u | head -40; echo "rc=$rc -> $OUT"
