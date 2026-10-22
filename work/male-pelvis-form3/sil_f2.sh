#!/bin/bash
# usage: sil_f2.sh <tag>  -> r/sil_<tag>/{bald_front,bald_back,left,right}.png via the blend's own workbench setup + gate numbers data/sil_<tag>.json
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form3
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
T=$1; SRC=data/V_$T.npy; [ "$T" = "start" ] && SRC=baseline/HeroBase_Male_Silhouette.blend
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python sil.py -- $SRC r/sil_$T 2>&1 | grep -E "Error|Traceback"
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 silgate.py r/sil_$T data/sil_$T.json
