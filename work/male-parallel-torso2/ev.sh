#!/bin/bash
# usage: ev.sh <tag> : plate-lit score, gate metric (Unity-clay), silhouettes, depth deficit, shelf creases
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=$1
$PY shlit.py $T 2>&1 | grep -E "under plate"
$B -b --factory-startup --python rt.py -- data/V_$T.npy r/${T}c front,back clay 2>&1 | grep -E "Error|Traceback"
$PY - <<PYEOF
import sys; sys.path.insert(0,'.')
from relcorr2 import *
import numpy as np
out={}
for v in ('front','back'):
    for rn,(z0,z1) in REG.items(): out[f'{v[0]}-{rn[:3]}']=round(corr_reg(v,'${T}c',z0,z1,0.12,1.2,5.0),3)
print('GATE metric (Unity-clay, DoG 1.2/5):', out, 'MEAN %.3f'%np.mean(list(out.values())))
PYEOF
$B -b --factory-startup --python sil.py -- data/V_$T.npy r/sil_$T 0 2>&1 | grep -E "Error|Traceback"
$PY silgate.py r/sil_$T r/sil_$T.json | sed 's/np.float64//g'
$PY depthdef.py $T 2>&1 | tail -1
$PY shards.py $T 55 2>&1 | sed -n 1,2p
