#!/bin/bash
# tools/run_editor.sh <ClassName> <out_dir>  — runs GolfArcade.EditorTools.<ClassName>.Run windowed + muted in ~/majestic-all-maps-UnityClone
# through heavy.sh. Copies every harness in work/majestic-all-maps/unity/Assets into the clone first. MAM_FRESH=1 re-clones Unity/.
# Extra env (MAM_HOLES, MAM_CAMS, DREAM_WEATHER, MAM_WITH_LAYER, ...) passes through.
# Note: the clone is reused between runs; MAM_FRESH=1 to drop a previous MAM_WITH_LAYER install.
set -u
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/majestic-all-maps-UnityClone
UNITY=/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity
CLS=$1; OUT=$(mkdir -p "$2" && cd "$2" && pwd)
[ -f "$OUT/unity.log" ] && mv "$OUT/unity.log" "$OUT/unity.prev.log"   # a stale log would trip the compile-error watchdog
if [ ! -d "$CLONE" ] || [ "${MAM_FRESH:-0}" = 1 ]; then rm -rf "$CLONE"; cp -cR "$ROOT/Unity" "$CLONE"; rm -rf "$CLONE/Temp"; fi
mkdir -p "$CLONE/Assets/Editor"; rsync -a "$ROOT/work/majestic-all-maps/unity/Assets/Editor/" "$CLONE/Assets/Editor/"
# MAM_WITH_LAYER=1: also install chat 10's Majestic course layer + the two hook lines into the clone (else the clone = Unity/ as is)
if [ "${MAM_WITH_LAYER:-0}" = 1 ]; then
  rsync -a --exclude Editor "$ROOT/work/majestic-all-maps/unity/Assets/" "$CLONE/Assets/"
  python3 "$ROOT/work/majestic-all-maps/tools/patch_majestic_hooks.py" "$CLONE/Assets"
  python3 "$ROOT/work/majestic-all-maps/tools/patch_g0_instancers.py" "$CLONE/Assets"
  # make-room: the same foliage kits at ~50 % triangles (g0/blender/lite.py), same object names, every distance
  cp "$ROOT/work/majestic-all-maps/g0/blender/lite/BotanicalKit.fbx" "$CLONE/Assets/Resources/Course/Resort/BotanicalKit.fbx"
  cp "$ROOT/work/majestic-all-maps/g0/blender/lite/CoastalBotany.fbx" "$CLONE/Assets/Resources/Course/Resort/CoastalBotany.fbx"
fi
if pgrep -f "projectPath $CLONE" >/dev/null; then echo "clone editor already running" >&2; exit 2; fi
GOLF_MUTE=1 MAM_OUT=$OUT "$ROOT/work/delegation-2026-10-17/heavy.sh" unity "$UNITY" -projectPath "$CLONE" -executeMethod GolfArcade.EditorTools.$CLS.Run -logFile "$OUT/unity.log" &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if grep -q "Scripts have compiler errors\|error CS" "$OUT/unity.log" 2>/dev/null; then grep "error CS" "$OUT/unity.log" | sort -u | head -8; pkill -f "projectPath $CLONE"; break; fi
  sleep 5
done
wait $PID; rc=$?; grep -E "error CS|\[Majestic[A-Za-z]*\]|Exception" "$OUT/unity.log" | sort -u | head -40; echo "rc=$rc -> $OUT"
