#!/bin/bash
# usage: graze.sh <tag> <outdir> <view spec> ; renders 4 graze lights (top, bottom, left, right) of the same view
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
T=$1; SRC=data/V_$T.npy; [ "$T" = "start" ] && SRC=baseline/HeroBase_Male_Silhouette.blend
i=0
for G in "0,0.5,0.85" "0,0.5,-0.85" "0.85,0.5,0.1" "-0.85,0.5,0.1"; do
  GRAZE=$G /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python rig.py -- $SRC r/$2_g$i "$3" clay 2>&1 | grep -E "Error|Traceback|bad view"
  i=$((i+1))
done
true
