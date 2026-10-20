import numpy as np
m_new = np.load('data/body_male_d6c4dcfb.npz'); m_old = np.load('data/fitref_male_old.npz')
Vn, Vo = m_new['V'], m_old['V']
d = np.linalg.norm(Vn - Vo, axis=1)
print('MALE same vert count', len(Vn) == len(Vo), 'max |dV| overall (mm)', d.max() * 1000)
for zmax in (0.10, 0.20, 0.30, 0.50, 0.70, 0.76, 0.80, 1.0):
    mk = Vo[:, 2] < zmax
    print(f'  verts z<{zmax}: n={mk.sum()}, max moved {1000*d[mk].max():.4f} mm, n moved>0.01mm: {(d[mk] > 1e-5).sum()}')
print('  first z where something moved:', Vo[d > 1e-5][:, 2].min() if (d > 1e-5).any() else None)
f = m_new['F']
# female: nearest distance new -> old surfaces (vertex-to-vertex is enough for rough)
f_new = np.load('data/body_female_a1d73a33.npz'); f_old = np.load('data/fitref_female_old.npz')
from math import inf
def foot_info(V, name):
    for side in (+1, -1):
        m = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.30)
        P = V[m]
        fm = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)
        Q = V[fm]
        print(f'{name} side {side:+d}: n(z<0.30)={m.sum()} x[{P[:,0].min():.4f},{P[:,0].max():.4f}] y[{P[:,1].min():.4f},{P[:,1].max():.4f}] z[{P[:,2].min():.5f},{P[:,2].max():.4f}] | footprint z<0.035: n={fm.sum()} y[{Q[:,1].min():.4f},{Q[:,1].max():.4f}] len={Q[:,1].max()-Q[:,1].min():.4f} x[{Q[:,0].min():.4f},{Q[:,0].max():.4f}]')
foot_info(m_new['V'], 'male NEW')
foot_info(f_new['V'], 'fem  NEW')
foot_info(f_old['V'], 'fem  OLD(200dc3b9)')
