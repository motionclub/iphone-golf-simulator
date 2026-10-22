#!/bin/bash
# Install the staged torso blend + FBX into ArtDir ONLY if ArtDir still holds the start SHAs (otherwise exit 2 -> rebase with apply_torso.py).
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-parallel-torso; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx
START_BL=68de53ca729ff04d366377e6df302952082abfb8e5621c524d39468c39f630cf; START_FBX=81276df06cbd136733e20232f388f860de71276d2487b22c508613d0a6e0aa43
STG_BL=$W/export/HeroBase_Male_Silhouette_torso.blend; STG_FBX=$W/export/HeroBase_Male_Body_torso.fbx
LOCK=$ART/blender/.install_lock_male_torso
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED by another installer: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
cur_bl=$(shasum -a 256 "$BL" | cut -d' ' -f1); cur_fbx=$(shasum -a 256 "$FBX" | cut -d' ' -f1)
echo "current blend $cur_bl"; echo "current fbx   $cur_fbx"
if [ "$cur_bl" != "$START_BL" ] || [ "$cur_fbx" != "$START_FBX" ]; then echo "ArtDir SHA changed since start -> NOT installing (rebase needed)"; exit 2; fi
mkdir -p "$W/baseline/pre_install"
cp -p "$BL" "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend"; cp -p "$FBX" "$W/baseline/pre_install/HeroBase_Male_Body.fbx"
[ "$(shasum -a 256 "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend" | cut -d' ' -f1)" = "$START_BL" ] || { echo backup blend mismatch; exit 4; }
[ "$(shasum -a 256 "$W/baseline/pre_install/HeroBase_Male_Body.fbx" | cut -d' ' -f1)" = "$START_FBX" ] || { echo backup fbx mismatch; exit 4; }
cp "$STG_BL" "$BL.torso.tmp"; cp "$STG_FBX" "$FBX.torso.tmp"
[ "$(shasum -a 256 "$BL.torso.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$STG_BL" | cut -d' ' -f1)" ] || { echo tmp blend mismatch; rm -f "$BL.torso.tmp" "$FBX.torso.tmp"; exit 5; }
# last-moment SHA re-check, then atomic replace
[ "$(shasum -a 256 "$BL" | cut -d' ' -f1)" = "$START_BL" ] || { echo "blend changed during install"; rm -f "$BL.torso.tmp" "$FBX.torso.tmp"; exit 2; }
mv -f "$BL.torso.tmp" "$BL"; mv -f "$FBX.torso.tmp" "$FBX"
echo "INSTALLED"; shasum -a 256 "$BL" "$FBX"
