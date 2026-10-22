#!/bin/bash
# usage: ARC=r2 CS=0.75 B=3.2 BANG=1.6 NB=0.8 LIPS=<lipskw json> run_p.sh <tag>
# r2 design: jaw as l2 but arc/chin settings from env; cheek = l2 settings; lips from LIPS (default l2 plan)
set -e
W=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head
cd $W; export PYTHONPATH=$W/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13; B_=/Applications/Blender.app/Contents/MacOS/Blender
LIPMODE_ARG=${LIPMODE_ARG:-}; TAG=$1; LIPSKW=${LIPS:-'{"strength":0.85}'}; LIPMOD=${LIPMOD:-lips}
WK='{"d_mouth":[6,26],"d_nose":[5,22],"d_eye":[8,26],"d_ear":[12,34],"z_lo":[1.482,1.500]}'
$PY run_l.py $TAG base=pre cheek=1.0 deflate3=5.0 jaw=1 trim=0.0 nboost=${NB:-0.8} nb_smooth_chin=${NBSC:-0} nchin_fair=${NCF:-0} nchin_fair_it=${NCFI:-4} lips=1 "cheekkw={\"iters\":220,\"wk\":$WK}" "deflate3kw={\"hollow\":3.0,\"gmin\":0.5,\"smooth\":8}" "jawkw={\"B\":${B:-3.2},\"sig_up\":${SU:-5.0},\"sig_up_ang\":11.0,\"sig_lo\":${SL:-4.5},\"drop\":${DROP:-0.0},\"B_ang\":${BANG:-1.6},\"dsm\":2,\"chin_scale\":${CS:-0.75},\"chin_t\":[0.06,0.30],\"arc\":\"${ARC:-r2}\",\"sig_up_chin\":${SUC:-null},\"sig_lo_chin\":${SLC:-null}}" "lipskw=$LIPSKW" $LIPMODE_ARG | tail -2
$B_ -b --factory-startup --python apply_j.py -- data/V_$TAG.npy data/N_$TAG.npy final/$TAG.blend 2>&1 | grep -E "Error|Traceback" || true
$B_ -b --factory-startup --python facem_lips.py -- final/$TAG.blend final/${TAG}f.blend "{\"seam_w\":1.6,\"seam_scale\":${SEAMS:-1.0},\"plan\":\"$W/data/lipplan_$TAG.json\"}" 2>&1 | grep -E "Error|Traceback" || true
$B_ -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f plate_front,plate_q3L,plate_q3R,plate_left,face_front,face_threequarter,face_profile,jaw_q 900 2>&1 | grep -E "Error|Traceback" || true
PLATE_UP=4 $B_ -b --factory-startup --python unity_like_j.py -- final/${TAG}f.blend r/ul_${TAG}f_p4 plate_front,plate_q3L,plate_q3R,plate_left,plate_right 1400 2>&1 | grep -E "Error|Traceback" || true
echo "run_p $TAG done"
