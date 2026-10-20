import json, itertools, subprocess, os, sys
LOW = [0.8, 1.0, 0.7, 0.4, 0.2, 0.08, 0, 0]
base = {'rbf': {'coef_file': 'data/c_PJ_i12.npz'}, 'allow_back': {'A': 8.0, 'z': [0.78, 0.805, 0.855, 0.90]}, 'only_struct': ['cleft2', 'lobes'], 'struct': {}}
spec = {}; n = 0
for A, x0, sx, z0 in itertools.product((8, 12), (0.05, 0.065, 0.08), (0.04, 0.055), (0.82, 0.85)):
    n += 1; spec[f'S{n:02d}'] = {'struct': {'cleft2': {f'a{i}': round(8 * v, 3) for i, v in enumerate(LOW)}, 'lobes': dict(A=A, x0=x0, sx=sx, z0=z0, sz=0.032)}}
json.dump(spec, open('spec_S.json', 'w')); json.dump(base, open('base_S.json', 'w')); print(len(spec), 'candidates')
