import json, random, sys
random.seed(11)
LOWS = {'low': [0.8, 1.0, 0.7, 0.4, 0.2, 0.08, 0, 0], 'lowc': [0.9, 1.0, 0.55, 0.28, 0.12, 0.03, 0, 0], 'lowd': [1.0, 1.0, 0.4, 0.15, 0.05, 0, 0, 0]}
spec = {}; meta = {}
for n in range(1, 61):
    shape = random.choice(list(LOWS)); A = round(random.uniform(5, 12), 1); lobA = round(random.uniform(3, 12), 1); x0 = round(random.uniform(0.04, 0.09), 3); sx = round(random.uniform(0.04, 0.08), 3); z0 = round(random.uniform(0.82, 0.88), 3); sz = round(random.uniform(0.026, 0.05), 3)
    tag = f'U{n:02d}'; meta[tag] = dict(shape=shape, A=A, lobA=lobA, x0=x0, sx=sx, z0=z0, sz=sz)
    spec[tag] = {'struct': {'cleft2': {f'a{i}': round(A * v, 3) for i, v in enumerate(LOWS[shape])}, 'lobes': dict(A=lobA, x0=x0, sx=sx, z0=z0, sz=sz)}}
json.dump(spec, open('spec_U.json', 'w')); json.dump(meta, open('meta_U.json', 'w'))
