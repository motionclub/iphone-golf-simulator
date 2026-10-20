#!/bin/bash
# usage: DROP=0.5 CS=0.5 B=3.2 BANG=1.6 run_d.sh <tag> [base] [hollow]   (cheek = l2 settings: deflate3 5.0/3.0 gmin 0.5 smooth 8; lips plan 0.85)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13; B_=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; BASE=${2:-5.0}; HOL=${3:-3.0}; DKW=${DKW:-'{}'}
WK='{"d_mouth":[6,26],"d_nose":[5,22],"d_eye":[8,26],"d_ear":[12,34],"z_lo":[1.482,1.500]}'
$PY run_l.py $TAG base=pre cheek=1.0 deflate3=$BASE jaw=1 trim=0.0 nboost=${NB:-0.8} lips=1 "cheekkw={\"iters\":220,\"wk\":$WK}" "deflate3kw={\"hollow\":$HOL,\"gmin\":0.5,\"smooth\":8}" "jawkw={\"B\":${B:-3.2},\"sig_up\":5.0,\"sig_up_ang\":11.0,\"sig_lo\":4.5,\"drop\":${DROP:-0.0},\"B_ang\":${BANG:-1.6},\"dsm\":2,\"chin_scale\":${CS:-0.5},\"chin_t\":[0.12,0.42],\"drop_kw\":$DKW}" 'lipskw={"strength":0.85}' | tail -2
$B_ -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B_ -b --factory-startup --python facem_lips.py -- final/$TAG.blend final/${TAG}f.blend "{\"seam_w\":1.6,\"plan\":\"$W/data/lipplan_$TAG.json\"}" 2>&1 | grep -E "Error|Traceback" || true
$B_ -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f plate_front,plate_q3L,plate_q3R,plate_left,face_front,face_threequarter,face_profile,jaw_q 900 2>&1 | grep -E "Error|Traceback" || true
echo "run_d $TAG done"
