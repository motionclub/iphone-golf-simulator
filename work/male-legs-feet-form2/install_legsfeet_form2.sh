#!/bin/bash
# Install the staged legs+feet FORM2 blend + FBX into ArtDir ONLY if ArtDir still holds the SHAs this edit was built on
# (otherwise exit 2 -> rebuild on the newer blend: extract_base.py, set BASE_TAG/BASE_BLEND/BASE_SHA in ff_common.py, build_all.py f1 design_v19.json, audit_ff.py).
set -e
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-legs-feet-form2; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx
START_BL=b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee; START_FBX=39303a777785a240ab9821107c00d9dfef6a476c29ce60d3bd369e7ad9e1038c
STG_BL=$W/export/HeroBase_Male_Silhouette_legsfeet_form2.blend; STG_FBX=$W/export/HeroBase_Male_Body_legsfeet_form2.fbx
NEW_BL=2e8f973b892b1e1bfba541341fa5d21b07565ddcf1aa23c7f4e09d93596bee3f; NEW_FBX=d40e9b55f7ae3bb1f0a11b62c77a65220eb9cba328ab49f25f89b1d086e2872a
LOCK=$ART/blender/.install_lock_male_legsfeet_form2
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
for l in "$ART"/blender/.install_lock_*; do [ -e "$l" ] && { echo "LOCKED by another installer: $l"; exit 3; }; done
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED by another installer: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
[ "$(sha "$STG_BL")" = "$NEW_BL" ] || { echo "staged blend is not the audited candidate"; exit 6; }
[ "$(sha "$STG_FBX")" = "$NEW_FBX" ] || { echo "staged fbx is not the audited candidate"; exit 6; }
cur_bl=$(sha "$BL"); cur_fbx=$(sha "$FBX")
echo "current blend $cur_bl"; echo "current fbx   $cur_fbx"
if [ "$cur_bl" != "$START_BL" ] || [ "$cur_fbx" != "$START_FBX" ]; then echo "ArtDir SHA changed since start -> NOT installing (rebuild needed)"; exit 2; fi
mkdir -p "$W/baseline/pre_install"
cp -p "$BL" "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend"; cp -p "$FBX" "$W/baseline/pre_install/HeroBase_Male_Body.fbx"
[ "$(sha "$W/baseline/pre_install/HeroBase_Male_Silhouette.blend")" = "$START_BL" ] || { echo backup blend mismatch; exit 4; }
[ "$(sha "$W/baseline/pre_install/HeroBase_Male_Body.fbx")" = "$START_FBX" ] || { echo backup fbx mismatch; exit 4; }
cp "$STG_BL" "$BL.legsfeet.tmp"; cp "$STG_FBX" "$FBX.legsfeet.tmp"
[ "$(sha "$BL.legsfeet.tmp")" = "$NEW_BL" ] || { echo tmp blend mismatch; rm -f "$BL.legsfeet.tmp" "$FBX.legsfeet.tmp"; exit 5; }
[ "$(sha "$FBX.legsfeet.tmp")" = "$NEW_FBX" ] || { echo tmp fbx mismatch; rm -f "$BL.legsfeet.tmp" "$FBX.legsfeet.tmp"; exit 5; }
# last-moment recheck: nobody installed while we were copying
[ "$(sha "$BL")" = "$START_BL" ] || { echo "blend changed during install"; rm -f "$BL.legsfeet.tmp" "$FBX.legsfeet.tmp"; exit 2; }
[ "$(sha "$FBX")" = "$START_FBX" ] || { echo "fbx changed during install"; rm -f "$BL.legsfeet.tmp" "$FBX.legsfeet.tmp"; exit 2; }
mv -f "$BL.legsfeet.tmp" "$BL"; mv -f "$FBX.legsfeet.tmp" "$FBX"
echo "INSTALLED"; shasum -a 256 "$BL" "$FBX"
