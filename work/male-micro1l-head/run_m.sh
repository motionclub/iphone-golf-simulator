#!/bin/bash
# usage: run_m.sh <tag> <sig_up_ang> <B_ang> <nboost> [B] [sig_up] [sig_lo] [chin_scale] -> data/V_<tag>.npy etc + final/<tag>.blend
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13; B=/Applications/Blender.app/Contents/MacOS/Blender
TAG=$1; SUA=$2; BANG=$3; NB=$4; BB=${5:-3.2}; SU=${6:-5.0}; SL=${7:-4.5}; CS=${8:-0.5}
WK='{"d_mouth":[6,26],"d_nose":[5,22],"d_eye":[8,26],"d_ear":[12,34],"z_lo":[1.482,1.500]}'
$PY run_l.py $TAG base=pre cheek=1.0 deflate=2.5 jaw=1 trim=0.0 nboost=$NB lips=1 "cheekkw={\"iters\":220,\"wk\":$WK}" "deflatekw={\"wk\":$WK}" "jawkw={\"B\":$BB,\"sig_up\":$SU,\"sig_up_ang\":$SUA,\"sig_lo\":$SL,\"drop\":0.0,\"B_ang\":$BANG,\"dsm\":2,\"chin_scale\":$CS,\"chin_t\":[0.12,0.42]}" 'lipskw={"low_fwd":0.0,"low_down":1.0}' | tail -2
$B -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
