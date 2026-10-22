#!/bin/bash
# SHA-guarded install of the FORM2 torso edit: merge by vertex-index patch onto the CURRENT ArtDir blend (never a whole-file overwrite of someone else's work).
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-parallel-torso2; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx; B=/Applications/Blender.app/Contents/MacOS/Blender
LOCK=$ART/blender/.install_lock_male_torso2
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED by another installer: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
cd $W
for attempt in 1 2 3; do
  S0=$(shasum -a 256 "$BL" | cut -d' ' -f1); F0=$(shasum -a 256 "$FBX" | cut -d' ' -f1); echo "attempt $attempt: ArtDir blend $S0  fbx $F0"
  BK=$W/baseline/pre_install_form2_${S0:0:8}.blend; BKF=$W/baseline/pre_install_form2_${F0:0:8}.fbx
  cp -p "$BL" "$BK"; cp -p "$FBX" "$BKF"
  [ "$(shasum -a 256 "$BK" | cut -d' ' -f1)" = "$S0" ] || { echo "backup mismatch (file changed while copying) -> retry"; continue; }
  M=$W/export/merged_${S0:0:8}.blend; MF=$W/export/merged_${S0:0:8}.fbx; MJ=$W/export/merged_${S0:0:8}.json
  $B -b --factory-startup --python-exit-code 1 --python apply_form2.py -- "$BK" "$M" 2>&1 | grep -E "APPLY_FORM2|ABORT|Error|Traceback"
  [ -f "$M" ] || { echo "merge produced no file (zone guard abort?)"; exit 4; }
  $B -b --factory-startup --python-exit-code 1 --python export_fbx.py -- "$M" "$MF" "$MJ" 2>&1 | grep -E "Error|Traceback|max_nearest"
  S1=$(shasum -a 256 "$BL" | cut -d' ' -f1)
  if [ "$S1" != "$S0" ]; then echo "ArtDir blend changed during the merge ($S0 -> $S1) -> redo on the new file"; rm -f "$M" "$MF"; continue; fi
  cp "$M" "$BL.form2.tmp"; cp "$MF" "$FBX.form2.tmp"
  [ "$(shasum -a 256 "$BL.form2.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$M" | cut -d' ' -f1)" ] || { echo "tmp copy mismatch"; rm -f "$BL.form2.tmp" "$FBX.form2.tmp"; exit 5; }
  S2=$(shasum -a 256 "$BL" | cut -d' ' -f1); [ "$S2" = "$S0" ] || { echo "changed at the last moment"; rm -f "$BL.form2.tmp" "$FBX.form2.tmp"; continue; }
  mv -f "$BL.form2.tmp" "$BL"; mv -f "$FBX.form2.tmp" "$FBX"
  echo "INSTALLED (merged onto $S0)"; shasum -a 256 "$BL" "$FBX"; echo "$S0" > $W/export/installed_over_blend_sha.txt; echo "$F0" > $W/export/installed_over_fbx_sha.txt; exit 0
done
echo "FAILED after 3 attempts"; exit 6
