#!/bin/bash
# usage: hand.sh <tag> <params.json>  -> build (np_model6), judge render, sil gate, pelvis judge sheets (back+3/4, side+front)
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin
export PYTHONPATH=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=$1; P=$2
$PY np_model6.py $P $T 2>&1 | grep -v -E "Warning|nanmean|^pin|^  [01]\."
unset PYTHONPATH
python3 judge.py render $T
VIEWS=back,q_bl,q_br ZOOM=3 python3 judge.py sheet tmp/jp_${T}.png pelvis $T | tail -1
./sil_np.sh $T
