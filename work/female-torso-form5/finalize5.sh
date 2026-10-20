#!/bin/bash
# Reproduce the whole FORM5 deliverable from START_form4_candidate.blend + the chest / glute / pelvis parameter jsons.
#   usage: bash finalize5.sh data/P5_final.json data/P_glute4.json data/PP5_final.json
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
EXPECT=aa3e1e443bd46201c18722cd6aa318c7c8de88b48787f473b9cfb5b63664e383
[ "$(shasum -a 256 START_form4_candidate.blend | cut -d' ' -f1)" = "$EXPECT" ] || { echo "START SHA MISMATCH -> STOP"; exit 1; }
ART=../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend
[ "$(shasum -a 256 $ART | cut -d' ' -f1)" = "200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd" ] || echo "WARNING: ArtDir female blend is no longer 200dc3b9 - rebase before installing"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
cp tools/merge_torso_delta.py export/merge_torso_delta.py
python3 tools/make_final5.py "${1:-data/P5_final.json}" "${2:-data/P_glute4.json}" "${3:-data/PP5_final.json}"
(cd gate7 && cp ../data/co_FORM5_final.npy data/torso_final.npy && python3 final_metrics.py >/dev/null && cp checks.json ../export/form5_gate_scripts_checks.json)
bash tools/verify_merge5.sh
python3 tools/readme_merge5.py
python3 tools/make_proofs5.py | tail -1
python3 tools/zoom4.py proof/05z_bust_zoom_soft.png soft FORM4=data/co_FORM4_final.npy FORM5=data/co_FORM5_final.npy | tail -1
python3 tools/zoom4.py proof/05z_bust_zoom_clay.png clay FORM4=data/co_FORM4_final.npy FORM5=data/co_FORM5_final.npy | tail -1
python3 tools/tri5.py proof/06z_underbutt_zoom_soft_clay.png pelvis --looks soft,clay F4=data/co_FORM4_final.npy F5=data/co_FORM5_final.npy | tail -1
python3 tools/foldtrace_plot6.py proof/06z_underbutt_zoom_soft_clay.png proof/06t_fold_line_trace.png | tail -1
python3 tools/tri5.py proof/05s_bust_zoom_stripe.png chest --looks stripe F4=data/co_FORM4_final.npy F5=data/co_FORM5_final.npy | tail -1
python3 tools/bpview5.py proof/08_bust_bandpass_vs_plate.png --gain 1.5 --sig 8 F4=data/co_FORM4_final.npy F5=data/co_FORM5_final.npy | tail -1
python3 tools/tri5.py scratch/_tmp_chest_soft.png chest --looks soft F4=data/co_FORM4_final.npy F5=data/co_FORM5_final.npy | tail -1   # soft renders read by the ring gate
python3 tools/gates5.py | tail -3
python3 tools/write_results5.py
rm -f export/*.blend1
shasum -a 256 export/HeroBase_Female_torso_form5_candidate.blend export/torso_form5_delta.npz "$ART"
