#!/bin/bash
# usage: build_l.sh <tag> [facem json]  -> final/<tag>.blend (Body_M + normals) and final/<tag>f.blend (+ lip paint rebuilt), previews r/ul_<tag>f
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; FJ=${2:-{\}}
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python facem_lips.py -- final/$TAG.blend final/${TAG}f.blend "$FJ" 2>&1 | grep -E "FACEM_LIPS|Error|Traceback" || true
$B -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f plate_front,plate_q3L,plate_q3R,plate_left,plate_right,face_front,face_threequarter,face_profile,face_threequarter_back,jaw_side,jaw_q 900 2>&1 | grep -E "Error|Traceback" || true
echo "build $TAG done"
