#!/bin/bash
# usage: gate_only.sh <tag> : clay render at the locked plate cameras + gate metric (6 regions), one line
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3
export PYTHONPATH=$PWD/../male-micro1i/pylib
B=/Applications/Blender.app/Contents/MacOS/Blender; PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
T=$1
$B -b --factory-startup --python rt.py -- data/V_$T.npy r/${T}c front,back clay 2>&1 | grep -E "Error|Traceback"
$PY - <<PYEOF 2>&1 | grep -v Warning
import sys; sys.path.insert(0,'.')
from relcorr2 import *
import numpy as np
out={}
for v in ('front','back'):
    for rn,(z0,z1) in REG.items(): out[f'{v[0]}-{rn[:3]}']=round(corr_reg(v,'${T}c',z0,z1,0.12,1.2,5.0),3)
print('${T:0:14}'.ljust(14), ' '.join(f'{k} {v:+.3f}' for k,v in out.items()), ' MEAN %.3f'%np.mean(list(out.values())))
PYEOF
