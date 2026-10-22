#!/bin/bash
# verify: ArtDir blend + torso_form5_delta == staged candidate (vertex arrays bit-identical); writes audit/artdir_plus_form5.json
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
B=/Applications/Blender.app/Contents/MacOS/Blender
ROOT="$HERE/../.."
cp "$ROOT/ArtDir/hero/base_lock/blender/HeroBase_Female.blend" scratch/artdir_copy.blend
$B -b scratch/artdir_copy.blend --python export/merge_torso_delta.py -- export/torso_form5_delta.npz scratch/artdir_plus_form5.blend 2>&1 | grep MERGE_REPORT | tee audit/merge_report.txt
$B -b scratch/artdir_plus_form5.blend --python tools/dump_blend.py -- audit/artdir_plus_form5.npz >/dev/null 2>&1
python3 - <<'PY'
import numpy as np, json
A=np.load('audit/artdir_plus_form5.npz'); Bz=np.load('audit/form5.npz')
ok=bool(np.array_equal(A['Body_F/co'],Bz['Body_F/co']))
okn=bool(np.array_equal(A['Body_F/custom_normal_raw'],Bz['Body_F/custom_normal_raw']))
print('ArtDir copy + delta == staged candidate (bit-identical vertices):',ok,' (custom-normal raw codes bit-identical):',okn)
json.dump({'artdir_plus_delta_equals_candidate':ok,'custom_normal_codes_equal_candidate':okn},open('audit/merge_verify.json','w'))
PY
# limbs-chat vertex order (22,419 verts): the same delta must apply through --vmap with 0 conflicts
LIMBS="$HERE/../female-parallel-limbs"
if [ -f "$LIMBS/HeroBase_Female_limbs.blend" ]; then
  cp "$LIMBS/HeroBase_Female_limbs.blend" scratch/limbs_copy.blend
  $B -b scratch/limbs_copy.blend --python export/merge_torso_delta.py -- export/torso_form5_delta.npz scratch/limbs_plus_form5.blend --vmap "$LIMBS/data/HeroBase_Female_limbs_vertex_map.npz" 2>&1 | grep MERGE_REPORT | tee audit/merge_report_limbs_order.txt
fi
rm -f scratch/*.blend scratch/*.blend1
