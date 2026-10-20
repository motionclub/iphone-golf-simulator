#!/bin/bash
# SHA-guarded install of the FORM3 torso edit: merge by vertex-index patch onto the CURRENT ArtDir blend (never a whole-file overwrite of other chats' work),
# verify the merge, re-export the FBX from the merged blend, then atomic move.  Lock: any .install_lock_* blocks us.
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-parallel-torso3; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx; B=/Applications/Blender.app/Contents/MacOS/Blender
LOCK=$ART/blender/.install_lock_male_torso3
for l in "$ART"/blender/.install_lock_*; do [ -e "$l" ] && { echo "LOCKED by another installer: $l"; exit 3; }; done
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
export PYTHONPATH=$W/../male-micro1i/pylib
cd $W
for attempt in 1 2 3; do
  S0=$(shasum -a 256 "$BL" | cut -d' ' -f1); F0=$(shasum -a 256 "$FBX" | cut -d' ' -f1); echo "attempt $attempt: ArtDir blend $S0  fbx $F0"
  BK=$W/baseline/pre_install_form3_${S0:0:8}.blend; BKF=$W/baseline/pre_install_form3_${F0:0:8}.fbx
  cp -p "$BL" "$BK"; cp -p "$FBX" "$BKF"
  [ "$(shasum -a 256 "$BK" | cut -d' ' -f1)" = "$S0" ] && [ "$(shasum -a 256 "$BKF" | cut -d' ' -f1)" = "$F0" ] || { echo "backup mismatch (file changed while copying) -> retry"; continue; }
  M=$W/export/merged_${S0:0:8}.blend; MF=$W/export/merged_${S0:0:8}.fbx; MJ=$W/export/merged_${S0:0:8}.json
  $B -b --factory-startup --python-exit-code 1 --python apply_form3.py -- "$BK" "$M" 2>&1 | grep -E "APPLY_FORM3|ABORT|Error|Traceback"
  [ -f "$M" ] || { echo "merge produced no file (zone guard abort?)"; exit 4; }
  $B -b --factory-startup --python-exit-code 1 --python verify_merge3.py -- "$BK" "$M" proof/male-torso-form3-install-verify.json 2>&1 | grep -E "VERIFY_MERGE3|Error|Traceback" | cut -c1-400
  [ "$(python3 -c "import json;print(json.load(open('proof/male-torso-form3-install-verify.json'))['PASS'])")" = "True" ] || { echo "merge verification FAILED"; exit 5; }
  $B -b --factory-startup --python-exit-code 1 --python export_fbx.py -- "$M" "$MF" "$MJ" 2>&1 | grep -E "Error|Traceback|max_nearest|imported_tris"
  $B -b --factory-startup --python normals3.py -- "$M" "$MF" proof/normals_form3_installed.json 2>&1 | grep -E "NORMALS|Error|Traceback" | cut -c1-500
  S1=$(shasum -a 256 "$BL" | cut -d' ' -f1)
  if [ "$S1" != "$S0" ]; then echo "ArtDir blend changed during the merge ($S0 -> $S1) -> redo on the new file"; rm -f "$M" "$MF"; continue; fi
  cp "$M" "$BL.form3.tmp"; cp "$MF" "$FBX.form3.tmp"
  [ "$(shasum -a 256 "$BL.form3.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$M" | cut -d' ' -f1)" ] && [ "$(shasum -a 256 "$FBX.form3.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$MF" | cut -d' ' -f1)" ] || { echo "tmp copy mismatch"; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; exit 6; }
  S2=$(shasum -a 256 "$BL" | cut -d' ' -f1); F2=$(shasum -a 256 "$FBX" | cut -d' ' -f1)
  if [ "$S2" != "$S0" ] || [ "$F2" != "$F0" ]; then echo "changed at the last moment -> redo"; rm -f "$BL.form3.tmp" "$FBX.form3.tmp"; continue; fi
  mv -f "$BL.form3.tmp" "$BL"; mv -f "$FBX.form3.tmp" "$FBX"
  echo "INSTALLED (merged onto $S0)"; shasum -a 256 "$BL" "$FBX"; echo "$S0" > $W/export/installed_over_blend_sha.txt; echo "$F0" > $W/export/installed_over_fbx_sha.txt
  shasum -a 256 "$BL" | cut -d' ' -f1 > $W/export/installed_blend_sha.txt; shasum -a 256 "$FBX" | cut -d' ' -f1 > $W/export/installed_fbx_sha.txt; exit 0
done
echo "FAILED after 3 attempts"; exit 6
