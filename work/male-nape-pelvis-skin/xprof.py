import sys; sys.path.insert(0,'.')
from common import *
tags=sys.argv[1:]
us=[0.0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10,0.12,0.14,0.16]
for z in (0.80,0.84,0.88,0.92):
    print(f'z={z:.2f} rear depth y(mm) vs |x|:  '+'  '.join(f'{u:.2f}' for u in us))
    for t in ['start']+tags:
        V=V0 if t=='start' else np.load(f'data/V_{t}.npy')
        row=[rear_curve(V,u+1e-5,np.array([z]))[0]*1000 for u in us]
        print(f'   {t:6s} '+'  '.join(f'{v:5.1f}' for v in row))
