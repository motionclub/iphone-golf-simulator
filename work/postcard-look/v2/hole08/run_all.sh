#!/bin/bash
# hole 8 Needle: stage build + every proof. Writes ONLY under work/postcard-look/v2/hole08/ (never blender/hole_08.blend, previews/, Unity/). ~6-12 minutes.
# Round 5 (repair round 1, 2026-10-04): 18 negative controls, relocated-copy texture check (2b), seam / ledge / lip / outcrop gates in the build, composition-scored arch camera.
# Round 6 (repair round 2, 2026-10-05): tee step (path cut + lift + riser, plate UV shift) gates TEE_SEAM_SEEN / PATH_STEP_CONTINUOUS, outcrop wall dressing gate ARCH_SLAB_COVERED, 22 negative controls.
# Round 7 (repair round 3, 2026-10-05): rebuild on the shared fixers' round-3 libs / textures (props lib: arch haunch recess, tapered stacks with waist, olive shrubs; verifier; Look PNGs Fairway / Green / Lava / Smoke); no hole-script change unless a gate needs it.
# Round 8 (repair round 0 of the GRASS LIVELINESS + GENTLE SWAY add-on, 2026-10-05): pad edge fringe (scatter_fringe) + island clumps + sea-stack crown tufts, the old tuft carpet cheapened to pay for them, the arch rim shoulder
# with smooth turf normals (ARCH_FOLD_SOFT), vines that touch the wall (attach_vines / sloped outcrop vines), the arch camera PINNED (make_landmarks.py --pin), grass gates GRASS_* / CROWN_TUFTS / VINE_ROOT_GAP / PLANT_SWAY_*, 33 negative controls.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
H=$R/work/postcard-look/v2/hole08
B=/Applications/Blender.app/Contents/MacOS/Blender
S=$H/stage; mkdir -p $S $H/logs $H/previews $H/scratch
cd $R
echo "== libs sha256 at this run" | tee $H/logs/lib_sha_final.txt
shasum -a 256 blender/scripts/postcard_look_lib.py blender/scripts/postcard_props_lib.py blender/scripts/postcard_look_verify.py blender/scripts/postcard_lib.py blender/scripts/golf_look_textures.py blender/scripts/hole08_build.py blender/scripts/hole08_look.py blender/scripts/hole08_design.py >> $H/logs/lib_sha_final.txt
shasum -a 256 Unity/Assets/Resources/Course/Look/*.png > $H/logs/look_png_sha_final.txt
# libs / verifier / textures unchanged since the round-2 reference run? (r2/lib_sha_ref.txt = the five foundation files at the start of round 2)
if [ -f $H/r3/logs_r2/look_png_sha_final.txt ]; then if diff -q $H/logs/look_png_sha_final.txt $H/r3/logs_r2/look_png_sha_final.txt > /dev/null 2>&1; then echo "Look PNGs: unchanged vs the round-2 run"; else echo "Look PNGs: CHANGED vs the round-2 run (r3/logs_r2/look_png_sha_final.txt): rebuild + re-measure is what this run does"; fi; fi
if [ -f $H/r2/lib_sha_ref.txt ]; then if diff -q <(sed -n 2,6p $H/logs/lib_sha_final.txt) $H/r2/lib_sha_ref.txt > /dev/null 2>&1; then echo "libs: unchanged vs r2/lib_sha_ref.txt"; else echo "libs: CHANGED vs r2/lib_sha_ref.txt (see logs/lib_sha_final.txt): rebuild is what this run does"; fi; fi
echo "== 1 build (stage)"; $B -b --factory-startup --python blender/scripts/hole08_build.py -- --out $S > $H/logs/build.log 2>&1; echo "build exit $?" | tee -a $H/logs/build.log
rm -f $S/hole_08.blend1
echo "== 2 postcard_look_verify (blend + FBX re-import)"; $B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 8 --blend $S/hole_08.blend --fbx $S/hole_08.fbx --json $H/logs/verify_look.json > $H/logs/verify_look.log 2>&1; echo "verify exit $?"
echo "== 2b relocated copy: the .blend must find its textures from another folder (absolute image paths; installed on blender/ it failed in round 4)"
rm -rf $H/scratch/relocated; mkdir -p $H/scratch/relocated/deeper; cp $S/hole_08.blend $S/hole_08.fbx $S/hole_08.fbx.meta $H/scratch/relocated/deeper/
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 8 --blend $H/scratch/relocated/deeper/hole_08.blend --fbx $H/scratch/relocated/deeper/hole_08.fbx --json $H/logs/verify_look_relocated.json > $H/logs/verify_look_relocated.log 2>&1; echo "relocated verify exit $?"; grep -E "LK_TEXTURED|^postcard_look_verify" $H/logs/verify_look_relocated.log | cut -c1-200
echo "== 3 postcard_verify"; $B -b $S/hole_08.blend --python blender/scripts/postcard_verify.py -- hole08_design --fbx $S/hole_08.fbx --json $H/logs/postcard_verify.json > $H/logs/postcard_verify.log 2>&1; echo "postcard_verify exit $?"
echo "== 4 postcard_check / emit_cs"; python3 blender/scripts/postcard_check.py hole08_design > $H/logs/postcard_check.log 2>&1; echo "postcard_check exit $?"; python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs > $H/logs/emit_cs_check.log 2>&1; echo "emit_cs exit $?"
echo "== 5 H_PLAY_UNCHANGED"; $B -b --factory-startup --python $H/tools/compare_baseline.py -- $S/hole_08.blend $H/logs/play_unchanged.json > $H/logs/play_unchanged.log 2>&1; grep GATE $H/logs/play_unchanged.log
echo "== 5b frame variation (albedo seen by the phone cameras) + dense path height (2 cm and 1 cm grids)"
$B -b --factory-startup --python $H/tools/frame_variation.py -- $S/hole_08.blend $H/logs/frame_variation.json --tag stage > $H/logs/frame_variation.log 2>&1; grep FRAMEVAR $H/logs/frame_variation.log | cut -c1-260
$B -b --factory-startup --python $H/tools/path_dense.py -- $S/hole_08.blend $H/logs/path_dense.json > $H/logs/path_dense.log 2>&1; grep PATHDENSE $H/logs/path_dense.log | cut -c1-200
$B -b --factory-startup --python $H/tools/path_dense.py -- $S/hole_08.blend $H/logs/path_dense_1cm.json --step 0.01 > $H/logs/path_dense_1cm.log 2>&1; grep PATHDENSE $H/logs/path_dense_1cm.log | cut -c1-200
echo "== 6 landmarks"; $B -b --factory-startup --python $H/tools/make_landmarks.py -- $S/hole_08.blend $H --pin > $H/logs/landmarks.log 2>&1; grep "LANDMARKS\|dense" $H/logs/landmarks.log
echo "== 6b arch fold on the FBX re-import, what the three still cameras see, fringe close views (Blender, NOT Game view)"
$B -b --factory-startup --python $H/tools/fbx_fold_check.py -- $S/hole_08.fbx $H/logs/fbx_fold.json > $H/logs/fbx_fold.log 2>&1; grep FBXFOLD $H/logs/fbx_fold.log | cut -c1-260
[ -f $H/r8/fbx_fold_before.json ] || $B -b --factory-startup --python $H/tools/fbx_fold_check.py -- $H/r8/stage_r7/hole_08.fbx $H/r8/fbx_fold_before.json > /dev/null 2>&1
$B -b --factory-startup --python $H/tools/frame_classes.py -- $S/hole_08.blend $H/logs/frame_classes.json > $H/logs/frame_classes.log 2>&1; grep FRAME $H/logs/frame_classes.log | cut -c1-220
mkdir -p $H/previews/fringe; $B -b --factory-startup --python $H/tools/fringe_views.py -- $S/hole_08.blend $H/previews/fringe > $H/logs/fringe_views.log 2>&1; python3 $H/tools/fringe_overlay.py $H/previews/fringe
echo "== 7 previews"; $B -b --factory-startup --python $H/tools/final_previews.py -- $S/hole_08.blend $H/previews $H/landmarks.json > $H/logs/previews.log 2>&1; python3 $H/tools/contact_sheet.py $H/previews; python3 $H/tools/sheet_round8.py
echo "== 7b H numbers + negative controls"; $B -b --factory-startup --python $H/tools/h_gates.py -- $S/hole_08.blend $S/hole_08.fbx $H/logs/h_numbers.json > $H/logs/h_numbers.log 2>&1; $B -b --factory-startup --python $H/tools/negctl.py 2>&1 | grep "NEGCTL\|BASE" | cut -c1-420 > $H/logs/negctl.txt; tail -1 $H/logs/negctl.txt
echo "== 8 reproducibility (two more builds, other PYTHONHASHSEED)"
for k in 1 2; do mkdir -p $H/scratch/repro$k; PYTHONHASHSEED=$((k*7)) $B -b --factory-startup --python blender/scripts/hole08_build.py -- --out $H/scratch/repro$k > $H/scratch/repro$k.log 2>&1; done
$B -b --factory-startup --python $H/tools/fingerprint_blend.py -- $S/hole_08.blend $H/scratch/repro1/hole_08.blend $H/scratch/repro2/hole_08.blend 2>&1 | grep "^FP" | tee $H/logs/reproducible.txt
echo "== 9 guards"; bash $R/work/postcard-look/guards.sh | tee $H/logs/guards.log
echo "== sha256 of the staged files"; (cd $S && shasum -a 256 hole_08.blend hole_08.fbx hole_08.fbx.meta) | tee $H/logs/stage_sha256.txt
echo "== 10 summary"; python3 $H/tools/summarize.py | tail -1
