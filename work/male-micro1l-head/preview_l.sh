#!/bin/bash
# usage: preview_l.sh <tag> [views]   -> final/<tag>.blend + r/ul_<tag>/*.png  (Unity-like, plate framings + face views)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; VIEWS=${2:-plate_front,plate_q3L,plate_q3R,plate_left,plate_right,face_front,face_threequarter,face_profile,jaw_side,jaw_q,chin_threequarter,face_threequarter_back}
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python unity_like_j.py -- final/$TAG.blend r/ul_$TAG $VIEWS 900 2>&1 | grep -E "Error|Traceback" || true
echo "preview $TAG done"
