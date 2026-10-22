#!/bin/bash
# Reproduce the whole FORM3 deliverable from START_form2_candidate.blend + a full parameter json.   usage: bash finalize3.sh data/P_final.json
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
EXPECT=6859d958982fa69beba4b48a44250a2f22a3b374d3caca4eb4717f5566a65f27
[ "$(shasum -a 256 START_form2_candidate.blend | cut -d' ' -f1)" = "$EXPECT" ] || { echo "START SHA MISMATCH -> STOP"; exit 1; }
ART=../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
[ "$(shasum -a 256 $ART | cut -d' ' -f1)" = "200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd" ] || echo "WARNING: ArtDir female blend is no longer 200dc3b9 - rebase before installing"
python3 tools/make_final3.py "${1:-data/P_final.json}"
(cd gate7 && cp ../data/co_FORM3_final.npy data/torso_final.npy && python3 final_metrics.py >/dev/null && cp checks.json ../export/form3_gate_scripts_checks.json)
python3 tools/readme_merge3.py
bash tools/verify_merge3.sh
python3 tools/gates3.py | tail -3
python3 tools/make_proofs3.py | tail -1
python3 tools/make_profiles3.py | tail -1
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b ../female-arms-form2/export/HeroBase_Female_arms_candidate.blend --python export/merge_torso_delta.py -- export/torso_form3_delta.npz export/PREVIEW_form3_torso_plus_limbs_plus_arms_UNOFFICIAL.blend --force --vmap ../female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz 2>&1 | grep MERGE_REPORT
python3 tools/render_merged3.py
python3 tools/write_results3.py
rm -f export/*.blend1
shasum -a 256 export/HeroBase_Female_torso_form3_candidate.blend export/torso_form3_delta.npz "$ART"
