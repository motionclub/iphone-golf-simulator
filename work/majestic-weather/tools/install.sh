#!/bin/bash
# tools/install.sh [--patch] [--remove] [Unity dir]   (default Unity dir: the repo's Unity/)
#   (no flag)  copy the weather layer's NEW files into Unity/ (Scripts/Majestic/MajesticWeather*.cs, Resources/Majestic/*Weather*).
#              On their own they stay dormant: the layer wakes only when the shader hook is in (next line).
#   --patch    also apply the shared-file edits (chat 6): EnvironmentSurface.hlsl hook, Weathers.SkyOf 10/16 -> ash, hook marker.
#   --remove   rollback: remove the shared-file edits and delete exactly the files this script installs.
set -eu
ROOT=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
W=$ROOT/work/majestic-weather
PATCH=0; REMOVE=0; DEST=$ROOT/Unity
for a in "$@"; do case "$a" in --patch) PATCH=1;; --remove) REMOVE=1;; *) DEST=$a;; esac; done
FILES="Scripts/Majestic/MajesticWeather.cs Scripts/Majestic/MajesticWeatherRules.cs Scripts/Majestic/MajesticWeatherFx.cs Scripts/Majestic/MajesticWeatherGlow.cs Scripts/Majestic/MajesticWeatherComet.cs
Resources/Majestic/MajesticWeather.hlsl Resources/Majestic/MajesticWeatherFall.shader Resources/Majestic/MajesticWeatherDrop.shader Resources/Majestic/MajesticWeatherSky.shader Resources/Majestic/MajesticWeatherReflect.shader Resources/Majestic/MajesticWeatherGlow.shader Resources/Majestic/MajesticWeatherComet.shader"
if [ $REMOVE = 1 ]; then
  python3 -I "$W/tools/patch_shared.py" remove "$DEST"
  for f in $FILES; do rm -f "$DEST/Assets/$f" "$DEST/Assets/$f.meta"; done
  echo "removed"; exit 0
fi
for f in $FILES; do
  mkdir -p "$(dirname "$DEST/Assets/$f")"
  cp "$W/unity/Assets/$f" "$DEST/Assets/$f"
  [ -f "$W/unity/Assets/$f.meta" ] && cp "$W/unity/Assets/$f.meta" "$DEST/Assets/$f.meta"
done
[ $PATCH = 1 ] && python3 -I "$W/tools/patch_shared.py" apply "$DEST"
( cd "$DEST/Assets" && shasum $FILES ) > "$W/INSTALLED.sha1"
echo "installed into $DEST (patch=$PATCH)"; cat "$W/INSTALLED.sha1"
