#!/bin/bash
# SHA-guarded install of the Micro1l head/neck/lip edit: vertex-index patch onto the CURRENT ArtDir blend (never a whole-file overwrite of other chats' work), lip paint strips rebuilt,
# verification, FBX re-export from the merged blend, last-moment SHA re-check, atomic move.  Lock: any .install_lock_* blocks us.
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator; W=$R/work/male-micro1l-head; ART=$R/ArtDir/hero/base_lock
BL=$ART/blender/HeroBase_Male_Silhouette.blend; FBX=$ART/unity_import/HeroBase_Male_Body.fbx; B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=${1:-l2}; FROM=${2:-}; FJ="{\"seam_w\":1.6,\"seam_scale\":${SEAM_SCALE:-1.0},\"plan\":\"$W/data/lipplan_$TAG.json\"}"
LOCK=$ART/blender/.install_lock_male_micro1l
for l in "$ART"/blender/.install_lock_*; do [ -e "$l" ] && { echo "LOCKED by another installer: $l"; exit 3; }; done
mkdir "$LOCK" 2>/dev/null || { echo "LOCKED: $LOCK"; exit 3; }
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
export PYTHONPATH=$W/pylib
cd $W
for attempt in 1 2 3; do
  S0=$(shasum -a 256 "$BL" | cut -d' ' -f1); F0=$(shasum -a 256 "$FBX" | cut -d' ' -f1); echo "attempt $attempt: ArtDir blend $S0  fbx $F0"
  BK=$W/baseline/pre_install_${TAG}_${S0:0:8}.blend; BKF=$W/baseline/pre_install_${TAG}_${F0:0:8}.fbx
  cp -p "$BL" "$BK"; cp -p "$FBX" "$BKF"
  [ "$(shasum -a 256 "$BK" | cut -d' ' -f1)" = "$S0" ] && [ "$(shasum -a 256 "$BKF" | cut -d' ' -f1)" = "$F0" ] || { echo "backup mismatch (file changed while copying) -> retry"; continue; }
  M1=$W/export/merged1_${TAG}_${S0:0:8}.blend; M=$W/export/merged_${TAG}_${S0:0:8}.blend; MF=$W/export/merged_${TAG}_${S0:0:8}.fbx; MJ=$W/export/merged_${TAG}_${S0:0:8}.json; AJ=$W/export/install_audit_${TAG}_${S0:0:8}.json
  $B -b --factory-startup --python-exit-code 1 --python merge_l.py -- "$BK" "$M1" $TAG $FROM 2>&1 | grep -E "MERGE_|Error|Traceback"
  [ -f "$M1" ] || { echo "merge produced no file (zone guard abort?)"; exit 4; }
  $B -b --factory-startup --python-exit-code 1 --python facem_lips.py -- "$M1" "$M" "$FJ" 2>&1 | grep -E "FACEM_LIPS|Error|Traceback" | cut -c1-140
  [ -f "$M" ] || { echo "Face_M lip rebuild produced no file"; exit 4; }
  $B -b --factory-startup --python-exit-code 1 --python audit_l.py -- "$M" "$AJ" export/install_audit_dir "$BK" 2>&1 | grep -E "AUDIT_JSON|SIL|Error|Traceback"
  OK=$(python3 - "$AJ" <<'EOF'
import json, sys
r = json.load(open(sys.argv[1])); sil = max(v['pct'] for v in r['silhouette'].values())
ok = (r['moved_outside_zone_z_lt_1_40'] == 0 and r['hands_moved'] == 0 and r['arms_moved'] == 0 and r['torso_pelvis_legs_feet_moved'] == 0 and r['topology_identical'] and r['vertex_groups_identical']
      and r['face_m_nonlip_slots_identical'] and sil <= 5.0 and not r['nan_or_inf'] and r['normals_far_from_edit']['changed_corners_gt_0_05deg'] == 0)
print('True' if ok else 'False')
EOF
)
  [ "$OK" = "True" ] || { echo "merge verification FAILED ($AJ)"; exit 5; }
  $B -b --factory-startup --python-exit-code 1 --python ../male-micro1h/export_final.py -- "$M" "$MF" "$MJ" 2>&1 | grep -E "EXPORT_JSON|Error|Traceback"
  [ -f "$MF" ] || { echo "FBX export produced no file"; exit 5; }
  OKF=$(python3 - "$MJ" <<'EOF'
import json, sys
r = json.load(open(sys.argv[1]))
print('True' if (r['Body_M']['max_reimport_mm'] < 0.01 and r['Face_M']['max_reimport_mm'] < 0.01 and len(r['face_slots']) == 13 and abs(r['Body_M']['height_m'] - 1.7022) < 0.01) else 'False')
EOF
)
  [ "$OKF" = "True" ] || { echo "FBX re-import verification FAILED ($MJ)"; exit 5; }
  S1=$(shasum -a 256 "$BL" | cut -d' ' -f1)
  if [ "$S1" != "$S0" ]; then echo "ArtDir blend changed during the merge ($S0 -> $S1) -> redo on the new file"; rm -f "$M1" "$M" "$MF"; continue; fi
  cp "$M" "$BL.l.tmp"; cp "$MF" "$FBX.l.tmp"
  [ "$(shasum -a 256 "$BL.l.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$M" | cut -d' ' -f1)" ] && [ "$(shasum -a 256 "$FBX.l.tmp" | cut -d' ' -f1)" = "$(shasum -a 256 "$MF" | cut -d' ' -f1)" ] || { echo "tmp copy mismatch"; rm -f "$BL.l.tmp" "$FBX.l.tmp"; exit 6; }
  S2=$(shasum -a 256 "$BL" | cut -d' ' -f1); F2=$(shasum -a 256 "$FBX" | cut -d' ' -f1)
  if [ "$S2" != "$S0" ] || [ "$F2" != "$F0" ]; then echo "changed at the last moment -> redo"; rm -f "$BL.l.tmp" "$FBX.l.tmp"; continue; fi
  mv -f "$BL.l.tmp" "$BL"; mv -f "$FBX.l.tmp" "$FBX"
  echo "INSTALLED (merged onto $S0)"; shasum -a 256 "$BL" "$FBX"; echo "$S0" > $W/export/installed_over_blend_sha.txt; echo "$F0" > $W/export/installed_over_fbx_sha.txt
  shasum -a 256 "$BL" | cut -d' ' -f1 > $W/export/installed_blend_sha.txt; shasum -a 256 "$FBX" | cut -d' ' -f1 > $W/export/installed_fbx_sha.txt; exit 0
done
echo "FAILED after 3 attempts"; exit 6
