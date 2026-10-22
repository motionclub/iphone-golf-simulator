#!/bin/bash
# Reproduce the whole FEMALE TORSO deliverable from the verified start blend.  Run from this folder:  bash run_all.sh
set -e
B=/Applications/Blender.app/Contents/MacOS/Blender
EXPECT=200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd
START=HeroBase_Female_torso.blend                         # byte-copy of ArtDir/hero/base_lock/blender/HeroBase_Female.blend (never edited)
[ "$(rm -f export/*.blend1
shasum -a 256 $START | cut -d' ' -f1)" = "$EXPECT" ] || { echo "START SHA MISMATCH -> STOP"; exit 1; }
mkdir -p data export audit proof/final
$B -b $START --python extract.py -- data/start.npz | grep -E "dumped"
python3 extract_side_profile.py
python3 zone.py
python3 fit_torso_final.py | tail -2
$B -b $START --python apply_coords_plain.py -- data/torso_final.npy export/HeroBase_Female_torso_candidate.blend | grep -E "saved"
python3 - <<'PY'
import numpy as np
d=np.load('data/start.npz'); co0=d['co']; z=np.load('data/zone.npz'); final=np.load('data/torso_final.npy').astype(np.float32)
moved=np.where((final!=co0.astype(np.float32)).any(1))[0]
np.savez_compressed('export/torso_delta.npz',moved_idx=moved.astype(np.int32),start_co=co0[moved].astype(np.float32),new_co=final[moved],zone_mask=z['torso'],weights=z['w'].astype(np.float32),vertex_count=np.int32(len(co0)))
print("delta: moved",len(moved))
PY
$B -b $START --python dump_blend.py -- audit/start.npz | grep dumped
$B -b export/HeroBase_Female_torso_candidate.blend --python dump_blend.py -- audit/cand.npz | grep dumped
python3 audit_zone.py | python3 -c "import json,sys; r=json.load(sys.stdin); print('OUTSIDE-ZONE AUDIT PASS =',r['PASS_outside_zone_equals_0'],'| moved outside zone =',r['moved_outside_zone'])"
python3 final_metrics.py
for t in start:$START final:export/HeroBase_Female_torso_candidate.blend; do tag=${t%%:*}; f=${t#*:}
  $B -b $f --python render_views.py -- proof/final/clay_$tag 1.08 0.80 clay_studio.exr front,q3F,side,q3B,back 640x860 >/dev/null
  $B -b $f --python render_views.py -- proof/final/refl_$tag 1.08 0.80 check_reflection_vertical.exr front,q3F,side,q3B,back 640x860 >/dev/null
  $B -b $f --python render_plate_frames.py -- proof/final/pf_$tag >/dev/null
  $B -b $f --python render_views.py -- proof/final/chest_$tag 1.22 0.50 clay_studio.exr front,y25,side 700x700 >/dev/null
  $B -b $f --python render_views.py -- proof/final/glute_$tag 0.92 0.55 clay_studio.exr back,y-155,side 700x700 >/dev/null
  $B -b $f --python render_views.py -- proof/final/q3_$tag 1.02 0.60 clay_studio.exr y25,y-25,y-155,y155 700x700 >/dev/null
done
python3 make_proofs.py
shasum -a 256 $START export/HeroBase_Female_torso_candidate.blend export/torso_delta.npz ../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
