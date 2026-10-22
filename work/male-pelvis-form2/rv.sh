#!/bin/bash
# usage: rv.sh <tag> <outdir> <spec,...> [look]   (tag: start | V tag) -> r/<outdir>/<spec>.png
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
T=$1; SRC=data/V_$T.npy; [ "$T" = "start" ] && SRC=baseline/HeroBase_Male_Silhouette.blend
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python rig.py -- $SRC r/$2 "$3" ${4:-clay} 2>&1 | grep -E "Error|Traceback|bad view"
true
