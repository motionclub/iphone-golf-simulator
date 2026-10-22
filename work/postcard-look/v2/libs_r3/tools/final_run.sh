#!/bin/bash
# libs repair round 3: the whole gate run on the FINAL lib files (Blender headless only; the Unity probe is a separate step: run_probe_scratch.sh). Writes only under work/postcard-look/v2/libs_r3/.
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
H=$R/work/postcard-look/v2/libs_r3
B=/Applications/Blender.app/Contents/MacOS/Blender
cd $R
shasum -a 256 blender/scripts/postcard_look_lib.py blender/scripts/postcard_props_lib.py blender/scripts/postcard_props_smoke.py blender/scripts/postcard_look_smoke.py Unity/Assets/Resources/Course/Look/Plants_C.png > $H/sha_final.txt
echo "== props smoke (full)"; $B -b --factory-startup --python blender/scripts/postcard_props_smoke.py -- --scratch $H/smoke_full --sheet $H/smoke_full/props_sheet.png > $H/smoke_full.log 2>&1; grep -E "^SUMMARY" $H/smoke_full.log
for h in 10 08 09; do
  echo "== look smoke hole $h"; $B -b --factory-startup --python blender/scripts/postcard_look_smoke.py -- --hole $h --out $H/lsmoke_hole$h --no-render > $H/lsmoke_hole$h.log 2>&1; echo "hole $h: $(grep -c '^GATE.* PASS' $H/lsmoke_hole$h.log) pass, $(grep -c '^GATE.* FAIL' $H/lsmoke_hole$h.log) fail"
done
for h in 08 09 10; do
  mkdir -p $H/h$h; echo "== scratch build hole $h"; $B -b --factory-startup --python blender/scripts/hole${h}_build.py -- --out $H/h$h --no-render > $H/h$h/build.log 2>&1 || $B -b --factory-startup --python blender/scripts/hole${h}_build.py -- --out $H/h$h > $H/h$h/build.log 2>&1
  echo "build gates FAIL lines: $(grep -c '^GATE.* FAIL' $H/h$h/build.log)"; grep -E "in-build gates|done: " $H/h$h/build.log | tail -1 | cut -c1-200
  $B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- ${h#0} --blend $H/h$h/hole_$h.blend --fbx $H/h$h/hole_$h.fbx --json $H/h$h/verify.json > $H/h$h/verify.log 2>&1; grep -E "^postcard_look_verify: hole|^RESULT" $H/h$h/verify.log | cut -c1-200
done
echo "== guards"; bash $R/work/postcard-look/guards.sh | grep -c PASS
