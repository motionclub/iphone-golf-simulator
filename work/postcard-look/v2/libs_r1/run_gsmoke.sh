#!/bin/bash
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
cd $R
B=/Applications/Blender.app/Contents/MacOS/Blender
V=work/postcard-look/v2/libs_r1
for h in 08 09 10; do
  /usr/bin/time -p $B -b --factory-startup --python blender/scripts/postcard_look_smoke.py -- --hole $h --out $R/$V/gsmoke/h$h --no-render > $V/gsmoke/h$h.log 2>&1
  echo "hole $h exit $?" >> $V/gsmoke/done.txt
done
echo ALLDONE >> $V/gsmoke/done.txt
