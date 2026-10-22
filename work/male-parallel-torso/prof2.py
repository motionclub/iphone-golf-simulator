import sys, numpy as np
from zone import *
tag = sys.argv[1]; side = sys.argv[2]; z0, z1 = float(sys.argv[3]), float(sys.argv[4])
V = np.load(f'data/V_{tag}.npy')
xs = [0.0, 0.06, 0.12, 0.18, 0.24]
print('z     ' + '  '.join(f'x~{x:.2f}' for x in xs))
for zf in np.arange(z0, z1, 0.01):
    row = []
    for xc in xs:
        m = (np.abs(V0[:, 2] - zf) < 0.0045) & (np.abs(np.abs(V0[:, 0]) - xc) < 0.012)
        if not m.any(): row.append('   --  '); continue
        yy = V[m, 1]; row.append(f'{(yy.max() if side=="back" else yy.min())*1000:7.1f}')
    print(f'{zf:.2f} ' + ' '.join(row))
