import sys, json, numpy as np
from pathlib import Path
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
import asm3
from hlib import *
prm = json.loads(sys.argv[1]); ids = [int(x) for x in sys.argv[2:]]
Vn, polys, si = asm3.assemble(prm, verbose=False)
info = si[+1]['info']; m = si[+1]['mapping']; inv = {v: b for b, v in m.items()}
role = {}
for r, lst in info['ring'].items():
    for i, v in enumerate(lst): role[v] = ('palm', r, i)
for k, (rows, C) in info['fin_rows'].items():
    for j, row in enumerate(rows):
        for i, v in enumerate(row): role[v] = ('finger', k, j, i)
    role[C] = ('fingertip', k)
for j, row in enumerate(info['thumb_rows']):
    for i, v in enumerate(row): role[v] = ('thumb', j, i)
role[info['thumb_tip']] = ('thumb_tip',)
for b in ids:
    bb = b if b in role else None
    print(b, role.get(b), 'final id', m.get(b))
print('hole rows/cols', info['P']['hole_rows'], info['P']['hole_cols'], 'C_loop', info['C_loop'])
