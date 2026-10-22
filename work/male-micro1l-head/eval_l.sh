#!/bin/bash
# usage: eval_l.sh <tag> [clay_light=top]   -> final/<tag>.blend, r/ul_<tag>, r/clay_<tag>/...
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; LIGHT=${2:-top}
./preview_l.sh $TAG plate_front,plate_q3L,plate_q3R,plate_left,plate_right,face_front,face_threequarter,face_profile,jaw_side,jaw_q 2>&1 | tail -1
$B -b --factory-startup --python clay_l.py -- r/clay_$TAG jaw_q,jaw_s,under_q $LIGHT cur:baseline/HeroBase_Male_Silhouette.9bfd788a.blend $TAG:final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
echo "eval $TAG done"
