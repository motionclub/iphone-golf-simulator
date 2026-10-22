#!/bin/bash
# verify: ArtDir blend + torso_form3_delta == staged candidate (vertex arrays bit-identical); writes audit/artdir_plus_form3.json
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
B=/Applications/Blender.app/Contents/MacOS/Blender
ROOT="$HERE/../.."
cp "$ROOT/ArtDir/hero/base_lock/blender/HeroBase_Female.blend" scratch/artdir_copy.blend
$B -b scratch/artdir_copy.blend --python export/merge_torso_delta.py -- export/torso_form3_delta.npz scratch/artdir_plus_form3.blend 2>&1 | grep MERGE_REPORT | tee audit/merge_report.txt
$B -b scratch/artdir_plus_form3.blend --python tools/dump_blend.py -- audit/artdir_plus_form3.npz >/dev/null 2>&1
python3 - <<'PY'
import numpy as np, json
A=np.load('audit/artdir_plus_form3.npz'); Bz=np.load('audit/form3.npz')
ok=bool(np.array_equal(A['Body_F/co'],Bz['Body_F/co']))
print('ArtDir copy + delta == staged candidate (bit-identical vertices):',ok)
json.dump({'artdir_plus_delta_equals_candidate':ok},open('audit/merge_verify.json','w'))
PY
rm -f scratch/*.blend scratch/*.blend1
