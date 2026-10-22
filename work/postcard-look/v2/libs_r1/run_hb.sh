#!/bin/bash
# scratch builds of the LIVE hole scripts against the repaired libs (output only under libs_r1/hb/, nothing installed)
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
cd $R
B=/Applications/Blender.app/Contents/MacOS/Blender
V=work/postcard-look/v2/libs_r1
for h in 08 09 10; do
  mkdir -p $V/hb/h$h
  /usr/bin/time -p $B -b --factory-startup --python blender/scripts/hole${h}_build.py -- --out $R/$V/hb/h$h > $V/hb/build$h.log 2>&1
  echo "hole $h exit $?" >> $V/hb/done.txt
done
echo ALLDONE >> $V/hb/done.txt
