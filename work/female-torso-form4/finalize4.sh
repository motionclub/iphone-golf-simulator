#!/bin/bash
# Reproduce the whole FORM4 deliverable from START_form3_candidate.blend + the chest / glute parameter jsons.
#   usage: bash finalize4.sh data/P_final4.json data/P_glute4.json
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
EXPECT=a0f69f9d0e8ee4cf0d9e441a56d2cfb99db99c3efe330b7c7974ac92c420dd46
[ "$(shasum -a 256 START_form3_candidate.blend | cut -d' ' -f1)" = "$EXPECT" ] || { echo "START SHA MISMATCH -> STOP"; exit 1; }
ART=../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
[ "$(shasum -a 256 $ART | cut -d' ' -f1)" = "200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd" ] || echo "WARNING: ArtDir female blend is no longer 200dc3b9 - rebase before installing"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cp tools/merge_torso_delta.py export/merge_torso_delta.py
python3 tools/make_final4.py "${1:-data/P_final4.json}" "${2:-data/P_glute4.json}"
(cd gate7 && cp ../data/co_FORM4_final.npy data/torso_final.npy && python3 final_metrics.py >/dev/null && cp checks.json ../export/form4_gate_scripts_checks.json)
python3 tools/readme_merge4.py
bash tools/verify_merge4.sh
python3 tools/make_proofs4.py | tail -1
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b ../female-arms-form2/export/HeroBase_Female_arms_candidate.blend --python export/merge_torso_delta.py -- export/torso_form4_delta.npz export/PREVIEW_form4_torso_plus_limbs_plus_arms_UNOFFICIAL.blend --force --vmap ../female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz 2>&1 | grep MERGE_REPORT
python3 tools/render_merged4.py
python3 tools/zoom4.py proof/05z_bust_zoom_soft.png soft FORM3=data/co_FORM3_final.npy FORM4=data/co_FORM4_final.npy | tail -1
python3 tools/zoom4.py proof/05z_bust_zoom_clay.png clay FORM3=data/co_FORM3_final.npy FORM4=data/co_FORM4_final.npy | tail -1
python3 tools/section.py front proof/08_bust_sections_front.png 1.16,1.19,1.21,1.23,1.25,1.27 data/orig_co.npy:original data/co_FORM3_final.npy:FORM3 data/co_FORM4_final.npy:FORM4 | tail -1
python3 tools/bpmap4.py proof/11_bandpass_maps.png FORM3=data/co_FORM3_final.npy FORM4=data/co_FORM4_final.npy | tail -1
python3 tools/side4.py proof/12_side_overlay_subpixel_zoom.png FORM3=data/co_FORM3_final.npy FORM4=data/co_FORM4_final.npy | tail -1
python3 tools/fullbody4.py proof/13_full_torso_soft.png soft FORM3=data/co_FORM3_final.npy FORM4=data/co_FORM4_final.npy | tail -1
python3 tools/gates4.py | tail -3
python3 tools/write_results4.py
rm -f export/*.blend1
shasum -a 256 export/HeroBase_Female_torso_form4_candidate.blend export/torso_form4_delta.npz "$ART"
