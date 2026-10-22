#!/bin/bash
# usage: evq3.sh <tag> : gate metric (Unity clay), plate-lit metric, silhouettes, depth rms, shelf contrast, shard count; renders skin + clay for closeups
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=$1
$PY shlit.py $T 2>&1 | grep -E "under plate" | sed "s/^/$T /"
$B -b --factory-startup --python rt.py -- data/V_$T.npy r/${T}c front,back clay 2>&1 | grep -E "Error|Traceback"
$B -b --factory-startup --python rt.py -- data/V_$T.npy r/$T front,back 2>&1 | grep -E "Error|Traceback"
$B -b --factory-startup --python sil.py -- data/V_$T.npy r/sil_$T 0 2>&1 | grep -E "Error|Traceback"
$PY - <<PYEOF 2>&1 | grep -v Warning
import sys; sys.path.insert(0,'.')
from relcorr2 import *
import numpy as np, silgate, pecprof_lib as PP
out={}
for v in ('front','back'):
    for rn,(z0,z1) in REG.items(): out[f'{v[0]}-{rn[:3]}']=round(corr_reg(v,'${T}c',z0,z1,0.12,1.2,5.0),3)
print('${T} GATE', out, 'MEAN %.3f'%np.mean(list(out.values())))
s=silgate.run('r/sil_${T}'); print('${T} SIL', {k:round(v['pct'],4) for k,v in s.items()})
pc=PP.measure(['base','${T}']); print('${T} PEC shelf (plate-lit):', {k:v for k,v in pc.items()})
PYEOF
$PY depthdef.py $T 2>&1 | tail -1 | sed "s/^/$T /"
$PY shards.py $T 55 2>&1 | sed -n 1,2p | sed "s/^/$T /"
