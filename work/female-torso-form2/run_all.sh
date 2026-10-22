#!/bin/bash
# Reproduce the whole FEMALE TORSO FORM2 deliverable from START_torso_candidate.blend + export/form2_params.json.  Run from this folder:  bash run_all.sh
set -e
B=/Applications/Blender.app/Contents/MacOS/Blender
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
EXPECT=696e1be464335e52db07444f16925a4d97f161b1a5b4927428a002b4945310e9
[ "$(shasum -a 256 START_torso_candidate.blend | cut -d' ' -f1)" = "$EXPECT" ] || { echo "START SHA MISMATCH -> STOP"; exit 1; }
python3 tools/make_final.py                                   # build coords, staged blend, delta, audit
cp data/torso_final.npy gate7/data/torso_final.npy
(cd gate7 && python3 final_metrics.py >/dev/null && cp checks.json ../export/form2_gate_scripts_checks.json)   # chat-7 gate scripts, unchanged
python3 - <<'PY'
import sys,json; sys.path.insert(0,'tools')
from featmetrics import *
P={**DEFAULT2,**json.load(open(WD/'export/form2_params.json'))}
co=np.load(WD/'data/co_FORM2_final.npy'); json.dump(metrics(co,P),open(WD/'export/form2_feature_metrics.json','w'),indent=1)
PY
python3 tools/gates.py | tail -1
AFTER=export/HeroBase_Female_torso_form2_candidate.blend; MC="$HERE/tools/soft_plate_matcap.png"; mkdir -p proof/final; F=$AFTER; t=after
$B -b $F --python tools/render_views.py -- proof/final/clay_$t 1.08 0.80 clay_studio.exr front,q3F,side,q3B,back 640x860 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/soft_$t 1.08 0.80 $MC front,q3F,side,q3B,back 640x860 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/chest_$t 1.22 0.50 $MC front,y25,y-25,side 700x700 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/chestC_$t 1.22 0.50 clay_studio.exr front,y25,y-25,side 700x700 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/glute_$t 0.92 0.55 $MC back,y-155,y155,side 700x700 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/gluteC_$t 0.92 0.55 clay_studio.exr back,y-155,y155,side 700x700 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/q3_$t 1.02 0.60 $MC y25,y-25,y-155,y155 700x700 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/stripeC_$t 1.22 0.40 check_reflection_vertical.exr front,y25,y-25 600x600 >/dev/null 2>&1
$B -b $F --python tools/render_views.py -- proof/final/stripeG_$t 0.92 0.46 check_reflection_vertical.exr back,y155,y-155 600x600 >/dev/null 2>&1
python3 tools/make_proofs2.py
# integration preview on the arms chat's candidate (limbs order) + install-path validation on a copy of the ArtDir blend
ROOT="$HERE/../.."
$B -b ../female-arms-form2/export/HeroBase_Female_arms_candidate.blend --python export/merge_torso_delta.py -- export/torso_form2_delta.npz export/PREVIEW_form2_torso_plus_limbs_plus_arms_UNOFFICIAL.blend --force --vmap ../female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz 2>&1 | grep MERGE_REPORT
cp "$ROOT/ArtDir/hero/base_lock/blender/HeroBase_Female.blend" proof/scratch/artdir_copy.blend
$B -b proof/scratch/artdir_copy.blend --python export/merge_torso_delta.py -- export/torso_form2_delta.npz proof/scratch/artdir_plus_form2.blend 2>&1 | grep MERGE_REPORT
$B -b proof/scratch/artdir_plus_form2.blend --python tools/dump_blend.py -- audit/artdir_plus_form2.npz >/dev/null 2>&1
python3 - <<'PY'
import numpy as np
A=np.load('audit/artdir_plus_form2.npz'); Bz=np.load('audit/form2.npz')
print('ArtDir copy + delta == staged candidate (bit-identical vertices):',bool(np.array_equal(A['Body_F/co'],Bz['Body_F/co'])))
PY
rm -f export/*.blend1 proof/scratch/*.blend proof/scratch/*.blend1
shasum -a 256 export/HeroBase_Female_torso_form2_candidate.blend export/torso_form2_delta.npz "$ROOT/ArtDir/hero/base_lock/blender/HeroBase_Female.blend"
