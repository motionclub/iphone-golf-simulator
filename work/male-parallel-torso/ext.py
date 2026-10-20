import sys, numpy as np
from zone import *
tags = sys.argv[1:]
Vs = {'base': V0}; 
for t in tags: Vs[t] = np.load(f'data/V_{t}.npy')
print('z    ' + '  '.join(f'{k:>6s}F {k:>6s}B' for k in Vs))
for zf in np.arange(0.76, 1.40, 0.02):
    row = []
    for k, V in Vs.items():
        m = (np.abs(V0[:, 2] - zf) < 0.006) & (np.abs(V0[:, 0]) < 0.05)
        row.append(f'{V[m,1].min()*1000:8.1f} {V[m,1].max()*1000:8.1f}')
    print(f'{zf:.2f} ' + ' | '.join(row))
