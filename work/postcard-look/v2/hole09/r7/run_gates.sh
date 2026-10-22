#!/bin/bash
# Runs every gate of the hole 9 staged build and writes the logs to work/postcard-look/v2/hole09/final/. usage: run_all_gates.sh [stage dir]
R="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"; cd "$R"
O=work/postcard-look/v2/hole09; F=$O/r7/gates_${LBL:-dev}; mkdir -p $F
S=${1:-$R/$O/stage}
B=/Applications/Blender.app/Contents/MacOS/Blender
echo "stage: $S"; shasum -a 256 $S/hole_09.blend $S/hole_09.fbx | tee $F/stage_sha256.txt
bash work/postcard-look/guards.sh > $F/guards.log 2>&1; echo "guards: $(grep -c PASS $F/guards.log)/7 PASS"
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs > $F/emit_check.log 2>&1; echo "emit --check exit $?"; tail -2 $F/emit_check.log
python3 blender/scripts/postcard_check.py $R/blender/scripts/hole09_design.py > $F/postcard_check.log 2>&1; echo "postcard_check exit $?"; tail -1 $F/postcard_check.log
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9 --blend $S/hole_09.blend --fbx $S/hole_09.fbx --json $F/look_verify.json > $F/look_verify.log 2>&1; echo "look_verify exit $?"; grep -E "^RESULT" $F/look_verify.log
$B -b $S/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design --fbx $S/hole_09.fbx --json $F/postcard_verify.json > $F/postcard_verify.log 2>&1; echo "postcard_verify exit $?"; grep -E "^RESULT|FAIL" $F/postcard_verify.log | cut -c1-240
$B -b --factory-startup --python blender/scripts/hole09_qa.py -- --blend $S/hole_09.blend --fbx $S/hole_09.fbx --json $F/hole09_qa.json > $F/hole09_qa.log 2>&1; echo "hole09_qa exit $?"; grep -E "^HOLE09_QA" $F/hole09_qa.log
$B -b --factory-startup --python work/postcard-look/v2/ground/tools/measure_blend.py -- --hole 09 --blend $S/hole_09.blend > $F/lib_audit.log 2>&1; echo "lib_audit exit $?"; grep -E "GATE|RESULT" $F/lib_audit.log | cut -c1-200
# repair round 1 (2026-10-04): the ruin masonry gates (independent of the construction records) on the blend and on the FBX re-import, and the tee seam measure on the preview
$B -b --factory-startup --python $O/tools/ruin_check.py -- --blend $S/hole_09.blend --json $F/ruin_check_blend.json > $F/ruin_check_blend.log 2>&1; echo "ruin_check blend exit $?"; grep -E "^GATE|^RUIN_CHECK" $F/ruin_check_blend.log | cut -c1-200
$B -b --factory-startup --python $O/tools/ruin_check.py -- --fbx $S/hole_09.fbx --json $F/ruin_check_fbx.json > $F/ruin_check_fbx.log 2>&1; echo "ruin_check fbx exit $?"; grep -E "^GATE|^RUIN_CHECK" $F/ruin_check_fbx.log | cut -c1-200
if [ -f $O/previews/hole09_tee.png ]; then $B -b --factory-startup --python $O/tools/seam_check.py -- $R/$O/previews/hole09_tee.png > $F/seam_check.log 2>&1; grep SEAM $F/seam_check.log; fi
$B -b --factory-startup --python $O/tools/collar_lie_check.py -- --blend $S/hole_09.blend > $F/collar_lie.log 2>&1; grep -E "^COLLAR" $F/collar_lie.log
# repair round 3 (2026-10-05): the texture jump the address camera sees across the far edge of the (10 cm raised) tee box
$B -b $S/hole_09.blend --python $O/tools/tee_parallax_check.py -- --json $F/tee_parallax.json > $F/tee_parallax.log 2>&1; grep -E "^GATE" $F/tee_parallax.log | cut -c1-260
