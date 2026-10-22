#!/bin/bash
# usage: run_c.sh <tag> <base> <hollow> [lowpass_alpha] [gmin] [smooth]   (jaw = m8 settings, cheek = deflate3)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13; B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; BASE=$2; HOL=$3; LA=${4:-1.0}; GM=${5:-0.35}; SM=${6:-6}
WK='{"d_mouth":[6,26],"d_nose":[5,22],"d_eye":[8,26],"d_ear":[12,34],"z_lo":[1.482,1.500]}'
$PY run_l.py $TAG base=pre cheek=$LA deflate3=$BASE jaw=1 trim=0.0 nboost=0.8 lips=1 "cheekkw={\"iters\":220,\"wk\":$WK}" "deflate3kw={\"hollow\":$HOL,\"gmin\":$GM,\"smooth\":$SM}" 'jawkw={"B":3.2,"sig_up":5.0,"sig_up_ang":11.0,"sig_lo":4.5,"drop":0.0,"B_ang":1.6,"dsm":2,"chin_scale":0.5,"chin_t":[0.12,0.42]}' 'lipskw={"strength":0.85}' | tail -2
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python facem_lips.py -- final/$TAG.blend final/${TAG}f.blend "{\"seam_w\":1.6,\"plan\":\"$W/data/lipplan_$TAG.json\"}" 2>&1 | grep -E "Error|Traceback" || true
PLATE_UP=4 $B -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f4 plate_front,plate_q3L,plate_q3R 1400 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f plate_front,plate_q3L,plate_q3R,plate_left,plate_right,face_front,face_threequarter,face_profile 900 2>&1 | grep -E "Error|Traceback" || true
echo "run_c $TAG done"
