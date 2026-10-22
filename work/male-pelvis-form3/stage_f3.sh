#!/bin/bash
# STAGE ONLY (never touches ArtDir): merge the FORM3 delta onto the CURRENT ArtDir blend, verify, export the FBX, check normals -> export/merged_<SHA8>.{blend,fbx,json}
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-pelvis-form3; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx; B=/Applications/Blender.app/Contents/MacOS/Blender
export PYTHONPATH=$W/../male-micro1i/pylib; export NP_DELTA=export/f3_delta.npz; cd $W
S0=$(shasum -a 256 "$BL" | cut -d' ' -f1); F0=$(shasum -a 256 "$FBX" | cut -d' ' -f1); echo "current ArtDir blend $S0  fbx $F0"
BK=$W/baseline/current_artdir_${S0:0:8}.blend; cp -p "$BL" "$BK"
M=$W/export/merged_${S0:0:8}.blend; MF=$W/export/merged_${S0:0:8}.fbx; MJ=$W/export/merged_${S0:0:8}.json
$B -b --factory-startup --python-exit-code 1 --python apply_f3.py -- "$BK" "$M" 2>&1 | grep -E "APPLY_F3|ABORT|Error|Traceback"
$B -b --factory-startup --python-exit-code 1 --python verify_merge_f3.py -- "$BK" "$M" export/install_verify_f3.json 2>&1 | grep -E "VERIFY_MERGE_F3|Error|Traceback" | cut -c1-600
$B -b --factory-startup --python-exit-code 1 --python ../male-micro1h/export_final.py -- "$M" "$MF" "$MJ" 2>&1 | grep -E "EXPORT_JSON|Error|Traceback"
$B -b --factory-startup --python normals_np.py -- "$M" "$MF" export/normals_staged_f3.json 2>&1 | grep -E "NORMALS|Error|Traceback" | cut -c1-500
shasum -a 256 "$M" "$MF"
