import json, random, subprocess, os, sys
import numpy as np
random.seed(7)
PYB = '/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'; env = dict(os.environ, PYTHONPATH='../male-micro1i/pylib')
LOWS = {'low': [0.8, 1.0, 0.7, 0.4, 0.2, 0.08, 0, 0], 'lowb': [0.6, 0.9, 1.0, 0.55, 0.25, 0.08, 0, 0], 'lowc': [0.9, 1.0, 0.55, 0.28, 0.12, 0.03, 0, 0]}
spec = {}; meta = {}
for n in range(1, 37):
    shape = random.choice(list(LOWS)); A = round(random.uniform(8, 16), 1); lobA = round(random.uniform(8, 14), 1); x0 = round(random.uniform(0.045, 0.08), 3); sx = round(random.uniform(0.035, 0.06), 3); z0 = round(random.uniform(0.82, 0.88), 3); sz = round(random.uniform(0.026, 0.04), 3)
    tag = f'R{n:02d}'; meta[tag] = dict(shape=shape, A=A, lobA=lobA, x0=x0, sx=sx, z0=z0, sz=sz)
    spec[tag] = {'struct': {'cleft2': {f'a{i}': round(A * v, 3) for i, v in enumerate(LOWS[shape])}, 'lobes': dict(A=lobA, x0=x0, sx=sx, z0=z0, sz=sz)}}
json.dump(spec, open('spec_R.json', 'w')); json.dump(meta, open('meta_R.json', 'w'))
