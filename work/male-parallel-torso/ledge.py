import sys, numpy as np
from zone import *
tag = sys.argv[1] if len(sys.argv) > 1 else 'base'
V = np.load(f'data/V_{tag}.npy')
print('unique z rings (0.74-0.90):', np.unique(np.round(V0[(V0[:,2]>0.74)&(V0[:,2]<0.90)&(np.abs(V0[:,0])<0.21),2],3)))
for xc in (0.0, 0.05, 0.10, 0.15, 0.185):
    print(f'--- |x|~{xc}')
    for zf in np.arange(0.74, 0.90, 0.01):
        m = (np.abs(V0[:, 2] - zf) < 0.0055) & (np.abs(np.abs(V0[:, 0]) - xc) < 0.012)
        if m.sum() < 2: continue
        print(f'  z {zf:.2f} n {m.sum():3d} front {V[m,1].min()*1000:7.1f} back {V[m,1].max()*1000:7.1f}   (base {V0[m,1].min()*1000:7.1f} {V0[m,1].max()*1000:7.1f})')
