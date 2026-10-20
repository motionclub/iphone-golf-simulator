#!/bin/bash
# Install the staged FORM3 hands blend + FBX into ArtDir ONLY if ArtDir still holds the start SHAs (otherwise exit 2 -> rebuild on the newer blend).
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-hands-form3; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx
START_BL=4287ba523218e89ae5a822483c322dc4cfa163c7af143ebcac11abbacea2db21; START_FBX=2d052746eb2ff26403080df24131abecd83564cf04528e77c46a9c2af245c483
STG_BL=$W/export/HeroBase_Male_Silhouette_form3.blend; STG_FBX=$W/export/HeroBase_Male_Body_form3.fbx
LOCK=$ART/blender/.install_lock_male_form3
for l in "$ART"/blender/.install_lock_*; do [ -e "$l" ] && { echo "LOCKED by another installer: $l"; exit 3; }; done
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED by another installer: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
cur_bl=$(shasum -a 256 "$BL" | cut -d' ' -f1); cur_fbx=$(shasum -a 256 "$FBX" | cut -d' ' -f1)
echo "current blend $cur_bl"; echo "current fbx   $cur_fbx"
if [ "$cur_bl" != "$START_BL" ] || [ "$cur_fbx" != "$START_FBX" ]; then echo "ArtDir SHA changed since start -> NOT installing (rebuild needed)"; exit 2; fi
mkdir -p "$W/baseline/pre_install"
cp -p "$BL" "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend"; cp -p "$FBX" "$W/baseline/pre_install/HeroBase_Male_Body.fbx"
[ "$(shasum -a 256 "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend" | cut -d' ' -f1)" = "$START_BL" ] || { echo backup blend mismatch; exit 4; }
[ "$(shasum -a 256 "$W/baseline/pre_install/HeroBase_Male_Body.fbx" | cut -d' ' -f1)" = "$START_FBX" ] || { echo backup fbx mismatch; exit 4; }
cp "$STG_BL" "$BL.form3.tmp"; cp "$STG_FBX" "$FBX.form3.tmp"
[ "$(shasum -a 256 "$BL.form3.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$STG_BL" | cut -d' ' -f1)" ] || { echo tmp blend mismatch; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; exit 5; }
[ "$(shasum -a 256 "$FBX.form3.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$STG_FBX" | cut -d' ' -f1)" ] || { echo tmp fbx mismatch; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; exit 5; }
[ "$(shasum -a 256 "$BL" | cut -d' ' -f1)" = "$START_BL" ] || { echo "blend changed during install"; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; exit 2; }
[ "$(shasum -a 256 "$FBX" | cut -d' ' -f1)" = "$START_FBX" ] || { echo "fbx changed during install"; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; exit 2; }
mv -f "$BL.form3.tmp" "$BL"; mv -f "$FBX.form3.tmp" "$FBX"
echo "INSTALLED"; shasum -a 256 "$BL" "$FBX"
