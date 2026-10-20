#!/bin/bash
# TENNIS_SHOES_FIT: full reproducible run.  SHA guard -> body dumps + foot landmarks -> socks -> shoes -> assemble -> gate measurements -> start-kit control -> proofs -> sheets -> report
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
cd $W
setopt null_glob 2>/dev/null || true
t0=$(date +%s)
step() { echo "== $1  (+$(( $(date +%s) - t0 ))s)"; }
check() { s=$(shasum -a 256 "$1" | cut -d' ' -f1); if [ "$s" != "$2" ]; then echo "SHA MISMATCH $1 -> $s"; exit 1; fi; echo "   sha ok $(basename $1) ${s:0:12}"; }
step "SHA guard (stop if any differs)"
check $R/work/male-pelvis-form3/export/merged_fd04bc28.blend d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781
check $R/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1
check start/StandardKit_Male.blend ad07a7b9ba984b0f220f975b9fe1b0c1b7068d9897c7e6f96e44f70d23aa77a9
check start/StandardKit_Female.blend f19a9c03789b7af343c56b005ed587137e8764779d31c3109942156ee71eaf4e
step "body dumps + foot landmarks"
$B -b --factory-startup $R/work/male-pelvis-form3/export/merged_fd04bc28.blend --python scripts/dump_body.py -- Body_M data/body_male_d6c4dcfb.npz 2>&1 | grep -E "Error|Trace" || true
$B -b --factory-startup $R/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend --python scripts/dump_body.py -- Body_F data/body_female_a1d73a33.npz 2>&1 | grep -E "Error|Trace" || true
$PY scripts/measure_feet.py > tmp/measure_feet.log
step "socks"; scripts/build_socks.sh male female
step "shoes"; scripts/build_shoes.sh male female | cut -c1-110
step "assemble"; for g in male female; do $B -b --factory-startup --python scripts/assemble_fit.py -- $g 2>&1 | grep -E "saved|Error|Trace|Assertion"; done
step "gate measurements"; for g in male female; do $B -b --factory-startup --python scripts/final_checks.py -- $g 2>&1 | grep -E "written|Error|Trace|Assertion"; done
step "start-kit control"; for g in male female; do $B -b --factory-startup --python scripts/fitcheck.py -- $g old 2>&1 | grep -E "Error|Trace" || true; cp tmp/fitcheck_${g}_old.json proof/raw/start_kit_on_new_body_${g}.json; done
step "proof cells"; scripts/run_proof_cells.sh
for g in male female; do
  G=$( [ $g = male ] && echo Male || echo Female ); if [ $g = male ]; then D=1.0; BB="$R/work/male-pelvis-form3/export/merged_fd04bc28.blend:Body_M"; else D=0.82; BB="$R/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend:Body_F"; fi
  for foot in R L; do VDIST=$D VTZ=0.095 VRES=640,640 $B -b --factory-startup --python scripts/view_blend.py -- start/StandardKit_$G.blend $g White proof/raw/before_${g}_White_$foot feet$foot --body "$BB" --parts shoes,socks 2>&1 | grep -E "Error|Trace" || true; done
  for cw in White Black; do VDIST=6.4 VLENS=105 VRES=520,760 $B -b --factory-startup --python scripts/view_blend.py -- export/StandardKit_$G.blend $g $cw proof/raw/context_${g}_${cw} full 2>&1 | grep -E "Error|Trace" || true; done
  $B -b --factory-startup --python scripts/render_cutaway.py -- $g White proof/raw/cut_${g}_White 2>&1 | grep -E "Error|Trace|tessellate failed" || true
done
step "sheets"; python3 scripts/compose_proofs.py
step "report"; python3 scripts/final_report.py
echo "ALL_DONE  (+$(( $(date +%s) - t0 ))s)"
