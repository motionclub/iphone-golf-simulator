#!/bin/bash
# usage: render_set.sh <tag> [look]   -> renders the standard comparison views for data/V_<tag>.npy into r/<tag>/
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
T=$1; LOOK=${2:-clay}
SRC=data/V_$T.npy; [ "$T" = "start" ] && SRC=baseline/HeroBase_Male_Silhouette.blend
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python rig.py -- $SRC r/$T "back@4,left@4,right@4,front@4,reg_q3BL_730_860_480_620_8,reg_q3BR_1010_1140_480_620_8,reg_q3FL_125_245_440_560_9,reg_q3FR_420_540_440_560_9,reg_q3BL_745_855_372_452_10,reg_q3BR_1030_1140_372_452_10,yaw90_0.5_1.40_0_560_800,yaw146_0.8_1.38_0_800_700" $LOOK 2>&1 | grep -E "Error|Traceback|bad view"
echo RENDERED $T
