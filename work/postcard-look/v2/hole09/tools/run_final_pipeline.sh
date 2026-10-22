#!/bin/bash
# end-to-end: staged build -> landmarks -> previews -> every gate -> reproducibility -> GATES_hole09.txt -> contact sheet -> sha256 list. Nothing is installed.
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; F=$O/final; B=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p $F
shasum -a 256 blender/scripts/postcard_look_lib.py blender/scripts/postcard_props_lib.py blender/scripts/postcard_lib.py blender/scripts/golf_look_textures.py blender/scripts/postcard_look_verify.py blender/scripts/hole09_design.py blender/scripts/postcard_check.py blender/scripts/postcard_emit_cs.py blender/scripts/hole09_build.py blender/scripts/hole09_look.py blender/scripts/hole09_masonry.py blender/scripts/hole09_stone.py blender/scripts/hole09_qa.py work/postcard-look/v2/hole09/tools/ruin_check.py work/postcard-look/v2/hole09/tools/tee_parallax_check.py work/postcard-look/v2/hole09/tools/grass_gates.py work/postcard-look/v2/hole09/tools/tuft_mask.py > $F/script_sha256_at_final_build.txt
(cd Unity/Assets/Resources/Course/Look && shasum -a 256 *.png) > $F/look_png_sha256_at_final_build.txt
$O/tools/run_build.sh final && cp $O/logs/build_final.log $F/build_final.log
$B -b --factory-startup --python $O/tools/make_landmarks.py -- --blend $R/$O/stage/hole_09.blend --out $O/landmarks.json > $F/make_landmarks.log 2>&1
rm -rf $O/previews; mkdir -p $O/previews
$B -b --factory-startup --python $O/tools/render_views.py -- --blend $R/$O/stage/hole_09.blend --json $R/$O/landmarks.json --out $R/$O/previews --samples 32 > $O/logs/render_final.log 2>&1
$B -b --factory-startup --python $O/tools/landmarks_check.py -- --blend $R/$O/stage/hole_09.blend --json $R/$O/landmarks.json --previews $R/$O/previews 2>&1 | grep -E "^GATE|LANDMARKS_CHECK|Traceback|Error" > $F/landmarks_check.log
$B -b --factory-startup --python $O/tools/tuft_mask.py -- --blend $R/$O/r8/before_r8/stage_r7/hole_09.blend --json $R/$O/landmarks.json --out $R/$O/r8/mask_before --label _before > $F/tuft_mask_before.log 2>&1
$O/tools/run_all_gates.sh > $F/run_all_gates.out 2>&1
rm -rf $O/stage_repro; mkdir -p $O/stage_repro; STAGE=$R/$O/stage_repro $O/tools/run_build.sh repro --no-render > /dev/null
RUIN_OLD_SUPPORT=1 $B -b --factory-startup --python $O/tools/ruin_check.py -- --blend $R/$O/stage/hole_09.blend 2>&1 | grep -E "^GATE: RUIN_SUPPORTED" > $F/ruin_check_old_support.log
$B -b --factory-startup --python $O/tools/ball_cover.py -- --blend $R/$O/stage/hole_09.blend --step 2.0 --json $R/$O/r5/evidence/ball_cover.json > $F/ball_cover.log 2>&1
$B -b --factory-startup --python blender/scripts/hole09_qa.py -- --blend $R/$O/stage_repro/hole_09.blend --json $F/hole09_qa_repro.json > $F/hole09_qa_repro.log 2>&1
$B -b --factory-startup --python $O/tools/fbx_hash.py -- $R/$O/stage/hole_09.fbx $R/$O/stage_repro/hole_09.fbx 2>&1 | grep FBXHASH > $F/repro_fbx_hash.txt
(cd $O && python3 tools/make_gates_txt.py > final/make_gates_txt.out 2>&1)
shasum -a 256 $O/stage/hole_09.blend $O/stage/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx.meta > $F/install_sha256.txt
echo done; cat $F/install_sha256.txt; tail -3 $F/make_gates_txt.out | cut -c1-300
