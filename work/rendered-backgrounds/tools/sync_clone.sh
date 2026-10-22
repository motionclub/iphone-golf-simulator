#!/bin/bash
# Install the rendered-backgrounds sources (work/rendered-backgrounds/unity) + assets + shared-file
# patches into a Unity project (default: the backgrounds clone). Idempotent.
#   tools/sync_clone.sh [unity_project]
set -eu
RB=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/rendered-backgrounds
DST=${1:-/private/tmp/backgrounds-UnityClone}
[ -d "$DST/Assets" ] || { echo "no Unity project at $DST" >&2; exit 2; }
# own files
rsync -a --exclude '*.meta' "$RB/unity/Assets/" "$DST/Assets/"
# metas we generated once in a clone are kept in unity/ too (stable GUIDs)
rsync -a --include '*/' --include '*.meta' --exclude '*' "$RB/unity/Assets/" "$DST/Assets/"
# assets rendered in Blender
R=$DST/Assets/Resources/Environment/RenderedSky; mkdir -p "$R"
for f in blender/clouds/CloudSixWay_A.png blender/clouds/CloudSixWay_B.png; do [ -f "$RB/$f" ] && cp "$RB/$f" "$R/"; done
[ -f "$RB/blender/clouds/clouds.json" ] && cp "$RB/blender/clouds/clouds.json" "$R/clouds.json"
for f in blender/cloudsea/CloudSea_A.png blender/cloudsea/CloudSea_B.png blender/cloudsea/CloudSea_Tint.png; do [ -f "$RB/$f" ] && cp "$RB/$f" "$R/"; done
for f in KarstIslands.fbx Karst_Albedo.png Karst_Normal.png; do [ -f "$RB/blender/karst/$f" ] && cp "$RB/blender/karst/$f" "$R/"; done
# shared-file patches (DreamEnvironment sky hook)
python3 "$RB/tools/patch_shared.py" "$DST"
echo "synced -> $DST"
