#!/bin/bash
# usage: run_n.sh <tag> <base> <hollow> [guard_hi] [lowpass_alpha]   (jaw = m8 settings)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13; B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; BASE=$2; HOL=$3; GH=${4:-0.18}; LA=${5:-1.0}
WK='{"d_mouth":[6,26],"d_nose":[5,22],"d_eye":[8,26],"d_ear":[12,34],"z_lo":[1.482,1.500]}'
$PY run_l.py $TAG base=pre cheek=$LA deflate2=$BASE jaw=1 trim=0.0 nboost=0.8 lips=1 "cheekkw={\"iters\":220,\"wk\":$WK}" "deflate2kw={\"wk\":$WK,\"hollow\":$HOL,\"guard_hi\":$GH}" 'jawkw={"B":3.2,"sig_up":5.0,"sig_up_ang":11.0,"sig_lo":4.5,"drop":0.0,"B_ang":1.6,"dsm":2,"chin_scale":0.5,"chin_t":[0.12,0.42]}' 'lipskw={"low_fwd":0.0,"low_down":1.0}' | tail -2
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python facem_lips.py -- final/$TAG.blend final/${TAG}f.blend '{"seam_w":1.9,"lo_h":11.4}' 2>&1 | grep -E "Error|Traceback" || true
$B -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f plate_front,plate_q3L,plate_q3R,plate_left,plate_right,face_front,face_threequarter,face_profile 900 2>&1 | grep -E "Error|Traceback" || true
echo "run_n $TAG done"
