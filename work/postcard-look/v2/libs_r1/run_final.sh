#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
cd $R
B=/Applications/Blender.app/Contents/MacOS/Blender
V=work/postcard-look/v2/libs_r1
for h in 08 09 10; do
  $B -b --factory-startup --python blender/scripts/postcard_look_smoke.py -- --hole $h --out $R/$V/gsmoke2/h$h --no-render > $V/gsmoke2/h$h.log 2>&1
  echo "gsmoke $h exit $?" >> $V/final_done.txt
done
for h in 08 09 10; do
  mkdir -p $V/hb2/h$h
  $B -b --factory-startup --python blender/scripts/hole${h}_build.py -- --out $R/$V/hb2/h$h > $V/hb2/build$h.log 2>&1
  echo "build $h exit $?" >> $V/final_done.txt
  n=$((10#$h))
  $B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- $n --blend $R/$V/hb2/h$h/hole_$h.blend --fbx $R/$V/hb2/h$h/hole_$h.fbx --json $R/$V/hb2/verify$h.json > $V/hb2/verify$h.log 2>&1
  echo "verify $h exit $?" >> $V/final_done.txt
done
echo ALLDONE >> $V/final_done.txt
