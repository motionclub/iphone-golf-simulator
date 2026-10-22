import sys; sys.path.insert(0,'.')
from common import *
zs = np.arange(1.26, 1.52, 0.01)
xs = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.15, 0.18]
print('REAR y (mm) by z (rows) and |x| (cols):', xs)
cur = {x: rear_curve(V0, x + 1e-5, zs) for x in xs}
for i, z in enumerate(zs):
    print(f'{z:.2f} ' + ' '.join(f'{cur[x][i]*1000:6.1f}' for x in xs))
print('FRONT y (mm)')
cur = {x: front_curve(V0, x + 1e-5, zs) for x in xs}
for i, z in enumerate(zs):
    print(f'{z:.2f} ' + ' '.join(f'{cur[x][i]*1000:6.1f}' for x in xs))
