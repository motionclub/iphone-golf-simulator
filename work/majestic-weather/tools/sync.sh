#!/bin/bash
# tools/sync.sh — make/refresh ~/majestic-weather-UnityClone: APFS clone of Unity/ (MW_FRESH=1 re-clones),
# copy this chat's new files + the proof harness in, apply the shared-file patch (clone only), frame timing stats on.
set -eu
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
CLONE=$HOME/majestic-weather-UnityClone
W=$ROOT/work/majestic-weather
if [ "${MW_FRESH:-0}" = 1 ]; then rm -rf "$CLONE"; fi
if [ ! -d "$CLONE" ]; then cp -cR "$ROOT/Unity" "$CLONE"; rm -rf "$CLONE"/{Temp,Logs,Builds}; fi
# the unpatched surface include, for the off-path proof (TOGGLE_RESTORES)
cp "$ROOT/Unity/Assets/Resources/Environment/Shaders/EnvironmentSurface.hlsl" "$W/proof/EnvironmentSurface.orig.hlsl"
# every file the shared patch touches, unpatched (the off-path proof swaps them all back at once)
for f in Resources/Environment/Shaders/EnvironmentSurface.hlsl Resources/Course/Shaders/GolfRock.shader Resources/Course/Shaders/GolfBotanical.shader \
         Resources/Course/Shaders/GolfOcean.shader Resources/Environment/LuminousCoast/CoastalPine.shader; do
  mkdir -p "$W/proof/orig/Assets/$(dirname $f)"; cp "$ROOT/Unity/Assets/$f" "$W/proof/orig/Assets/$f"; done
rsync -a "$W/unity/Assets/" "$CLONE/Assets/"
python3 -I "$W/tools/patch_shared.py" apply "$CLONE"
# original-shader twins for the same-frame off-path proof (clone only)
python3 -I "$W/tools/make_orig.py" "$ROOT/Unity" "$CLONE"
sed -i '' 's/enableFrameTimingStats: 0/enableFrameTimingStats: 1/' "$CLONE/ProjectSettings/ProjectSettings.asset"
echo synced
