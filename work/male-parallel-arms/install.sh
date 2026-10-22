#!/bin/bash
# Install the staged arms/hands blend + FBX into ArtDir ONLY if ArtDir still holds the S1 SHAs (otherwise exit 2 -> rebase with apply_delta.py).
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-parallel-arms; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx
START_BL=b9cc85967819b5fc31d323c0aa806c925a9e2e849b878e31c1866a2a8404909c; START_FBX=8646290043ef08e67bf22b1bd78f22c5ae8dc8f228ce41ec9d81b349899ecbff
STG_BL=$W/export/HeroBase_Male_Silhouette_arms.blend; STG_FBX=$W/export/HeroBase_Male_Body_arms.fbx
LOCK=$ART/blender/.install_lock_male_arms
for l in "$ART"/blender/.install_lock_*; do [ -e "$l" ] && { echo "LOCKED by another installer: $l"; exit 3; }; done
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED by another installer: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
cur_bl=$(shasum -a 256 "$BL" | cut -d' ' -f1); cur_fbx=$(shasum -a 256 "$FBX" | cut -d' ' -f1)
echo "current blend $cur_bl"; echo "current fbx   $cur_fbx"
if [ "$cur_bl" != "$START_BL" ] || [ "$cur_fbx" != "$START_FBX" ]; then echo "ArtDir SHA changed since start -> NOT installing (rebase needed)"; exit 2; fi
mkdir -p "$W/baseline_S1/pre_install"
cp -p "$BL" "$W/baseline_S1/pre_install/HeroBase_Male_Silhouette.blend"; cp -p "$FBX" "$W/baseline_S1/pre_install/HeroBase_Male_Body.fbx"
[ "$(shasum -a 256 "$W/baseline_S1/pre_install/HeroBase_Male_Silhouette.blend" | cut -d' ' -f1)" = "$START_BL" ] || { echo backup blend mismatch; exit 4; }
[ "$(shasum -a 256 "$W/baseline_S1/pre_install/HeroBase_Male_Body.fbx" | cut -d' ' -f1)" = "$START_FBX" ] || { echo backup fbx mismatch; exit 4; }
cp "$STG_BL" "$BL.arms.tmp"; cp "$STG_FBX" "$FBX.arms.tmp"
[ "$(shasum -a 256 "$BL.arms.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$STG_BL" | cut -d' ' -f1)" ] || { echo tmp blend mismatch; rm -f "$BL.arms.tmp" "$FBX.arms.tmp"; exit 5; }
[ "$(shasum -a 256 "$FBX.arms.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$STG_FBX" | cut -d' ' -f1)" ] || { echo tmp fbx mismatch; rm -f "$BL.arms.tmp" "$FBX.arms.tmp"; exit 5; }
# last-moment SHA re-check, then atomic replace
[ "$(shasum -a 256 "$BL" | cut -d' ' -f1)" = "$START_BL" ] || { echo "blend changed during install"; rm -f "$BL.arms.tmp" "$FBX.arms.tmp"; exit 2; }
[ "$(shasum -a 256 "$FBX" | cut -d' ' -f1)" = "$START_FBX" ] || { echo "fbx changed during install"; rm -f "$BL.arms.tmp" "$FBX.arms.tmp"; exit 2; }
mv -f "$BL.arms.tmp" "$BL"; mv -f "$FBX.arms.tmp" "$FBX"
echo "INSTALLED"; shasum -a 256 "$BL" "$FBX"
