#!/bin/bash
# run_all.sh: the whole hole 10 staging + gate run (Blender headless only, no Unity, nothing written outside work/postcard-look/v2/hole10/).
#   work/postcard-look/v2/hole10/tools/run_all.sh
# Round 3 (2026-10-04): + H_CRUST / H_GLOW_JOINTS / H_CONE_GLOW stage gates, round-2 reference renders, three-round sheets.
# Order: lib sha256 snapshot -> guards -> staged build (--out stage) -> reproducibility build (--out stage_repro) -> verifier on blend + FBX ->
# postcard_verify -> postcard_check -> emit_cs --check -> stage gates -> H_PLAY_UNCHANGED -> landmark rays -> previews + sheets -> lib sha256 re-check -> sha256 of the staged files.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
B=/Applications/Blender.app/Contents/MacOS/Blender
S=$R/work/postcard-look/v2/hole10
T=$S/tools
L=$S/logs
STAGE=$S/stage
REPRO=$S/stage_repro
mkdir -p "$L" "$STAGE" "$REPRO"
cd "$R" || exit 1
LIBS="blender/scripts/postcard_look_lib.py blender/scripts/postcard_props_lib.py blender/scripts/postcard_look_verify.py blender/scripts/postcard_lib.py blender/scripts/golf_look_textures.py"
shasum -a 256 $LIBS Unity/Assets/Resources/Course/Look/*.png > "$L/libs_sha_before.txt"
date > "$L/run_started.txt"

echo "== guards (hole 7, Hole.cs, GolfGame)"; bash work/postcard-look/guards.sh > "$L/guards_before.txt" 2>&1; cat "$L/guards_before.txt" | sed 's/^/   /'

echo "== staged build"; rm -f "$STAGE"/hole_10.* "$STAGE"/*.png
$B -b --factory-startup --python blender/scripts/hole10_build.py -- --out "$STAGE" > "$L/build_stage.log" 2>&1; echo "   exit $?"
grep -E "^GATE: (H_|LIB_)|\[hole10_build\]" "$L/build_stage.log" | cut -c1-260

echo "== reproducibility build (second --out dir, no render)"; rm -f "$REPRO"/hole_10.*
$B -b --factory-startup --python blender/scripts/hole10_build.py -- --out "$REPRO" --no-render > "$L/build_repro.log" 2>&1; echo "   exit $?"

echo "== postcard_look_verify (blend + FBX re-import)"
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 10 --blend "$STAGE/hole_10.blend" --fbx "$STAGE/hole_10.fbx" --json "$L/look_verify.json" > "$L/look_verify.log" 2>&1; echo "   exit $?"
grep -E "^RESULT" "$L/look_verify.log"

echo "== postcard_verify (blend + FBX)"
$B -b "$STAGE/hole_10.blend" --python blender/scripts/postcard_verify.py -- hole10_design --fbx "$STAGE/hole_10.fbx" --json "$L/postcard_verify.json" > "$L/postcard_verify.log" 2>&1; echo "   exit $?"
grep -E "^RESULT" "$L/postcard_verify.log"

echo "== postcard_check (design, pure python)"
python3 blender/scripts/postcard_check.py ./blender/scripts/hole10_design.py > "$L/postcard_check.log" 2>&1; echo "   exit $?"; tail -3 "$L/postcard_check.log"
echo "== postcard_emit_cs --check"
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs > "$L/emit_cs_check.log" 2>&1; echo "   exit $?"; tail -2 "$L/emit_cs_check.log"
python3 blender/scripts/hole10_design.py > "$L/design_verify.log" 2>&1; echo "   design --verify exit $?"; tail -1 "$L/design_verify.log"

echo "== stage gates (blend + FBX)"
$B -b "$STAGE/hole_10.blend" --python $T/stage_gates.py -- --blend "$STAGE/hole_10.blend" --fbx "$STAGE/hole_10.fbx" --json "$L/stage_gates.json" > "$L/stage_gates.log" 2>&1; echo "   exit $?"
grep -E "^RESULT" "$L/stage_gates.log"
echo "== H_PLAY_UNCHANGED"
$B -b "$STAGE/hole_10.blend" --python $T/play_unchanged.py > "$L/play_unchanged.log" 2>&1; echo "   exit $?"; grep -E "^GATE" "$L/play_unchanged.log" | cut -c1-200
echo "== landmark rays"
$B -b "$STAGE/hole_10.blend" --python $T/landmark_check.py -- --shots $S/landmarks.json --json "$L/landmark_check.json" > "$L/landmark_check.log" 2>&1; echo "   exit $?"; grep -E "^RESULT" "$L/landmark_check.log"

echo "== previews (Blender EEVEE with the Unity-like material / sky / fog / lava-light patch of tools/render_views.py, NOT Game view)"
rm -rf "$S/previews"; mkdir -p "$S/previews"
J=$S/landmarks_with_aerial.json
$B -b "$STAGE/hole_10.blend" --python $T/render_views.py -- --shots $J --out "$S/previews" --only tee,approach,lavarim --prefix "" > "$L/previews.log" 2>&1
$B -b "$STAGE/hole_10.blend" --python $T/render_views.py -- --shots $J --out "$S/previews" --only aerial,aerial2,aerial3,aerial4,wallclose,wallclose2,cone --res 1600x900 >> "$L/previews.log" 2>&1
$B -b "$STAGE/hole_10.blend" --python $T/render_views.py -- --shots $J --out "$S/previews" --only plan --res 1000x1000 --mask --samples 1 --prefix "mask_" >> "$L/previews.log" 2>&1
# round-1 reference renders (same tool, same cameras), made once
if [ ! -f "$S/round1/pv/hole10_tee.png" ]; then
  mkdir -p "$S/round1/pv"
  $B -b "$S/round1/hole_10_round1.blend" --python $T/render_views.py -- --shots $J --out "$S/round1/pv" --only tee,approach,lavarim --prefix "" > "$L/previews_round1.log" 2>&1
  $B -b "$S/round1/hole_10_round1.blend" --python $T/render_views.py -- --shots $J --out "$S/round1/pv" --only aerial,aerial2,aerial3,aerial4,wallclose,wallclose2 --res 1600x900 >> "$L/previews_round1.log" 2>&1
  $B -b "$S/round1/hole_10_round1.blend" --python $T/render_views.py -- --shots $J --out "$S/round1/pv" --only plan --res 1000x1000 --mask --samples 1 --prefix "mask_" >> "$L/previews_round1.log" 2>&1
fi
if [ ! -f "$S/round2/pv/hole10_tee.png" ]; then
  mkdir -p "$S/round2/pv"
  $B -b "$S/round2/hole_10_round2.blend" --python $T/render_views.py -- --shots $J --out "$S/round2/pv" --only tee,approach,lavarim --prefix "" > "$L/previews_round2.log" 2>&1
  $B -b "$S/round2/hole_10_round2.blend" --python $T/render_views.py -- --shots $J --out "$S/round2/pv" --only aerial,aerial2,aerial3,aerial4,wallclose,wallclose2,cone --res 1600x900 >> "$L/previews_round2.log" 2>&1
  $B -b "$S/round2/hole_10_round2.blend" --python $T/render_views.py -- --shots $J --out "$S/round2/pv" --only plan --res 1000x1000 --mask --samples 1 --prefix "mask_" >> "$L/previews_round2.log" 2>&1
fi
echo "== H_OPEN_LAVA (mask renders of the 4 aerial cameras, stage vs round 1)"
bash $T/open_lava.sh "$STAGE/hole_10.blend" "$L/open_lava.log" | cut -c1-300
echo "== H_TEE_SEAM_PREVIEW (row-step seam metric on the Blender tee preview; the Game-view number needs Unity)"
$B -b --factory-startup --python $T/seam_metric.py -- "$S/previews/hole10_tee.png" --json "$L/seam.json" > "$L/seam.log" 2>&1; grep -E "^GATE" "$L/seam.log" | cut -c1-260
python3 $T/make_sheets.py > "$L/sheets.log" 2>&1; echo "   sheets exit $?"

shasum -a 256 $LIBS Unity/Assets/Resources/Course/Look/*.png > "$L/libs_sha_after.txt"
if diff -q "$L/libs_sha_before.txt" "$L/libs_sha_after.txt" > /dev/null; then echo "== libs unchanged during the run: yes"; else echo "== LIBS CHANGED DURING THE RUN: rebuild"; diff "$L/libs_sha_before.txt" "$L/libs_sha_after.txt"; fi
bash work/postcard-look/guards.sh > "$L/guards_after.txt" 2>&1; echo "== guards after: $(grep -c PASS "$L/guards_after.txt") PASS of $(wc -l < "$L/guards_after.txt")"
shasum -a 256 "$STAGE/hole_10.blend" "$STAGE/hole_10.fbx" > "$S/stage_sha256.txt"; ls -l "$STAGE" | sed 's/^/   /'; cat "$S/stage_sha256.txt"
date >> "$L/run_started.txt"
