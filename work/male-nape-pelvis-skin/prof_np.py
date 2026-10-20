"""print rear sagittal profiles start vs candidate: python3.13 prof_np.py <tag> [u list]"""
import sys; sys.path.insert(0,'.')
from common import *
tag = sys.argv[1]; V1 = np.load(f'data/V_{tag}.npy')
us = [float(a) for a in sys.argv[2:]] or [0.0, 0.04, 0.08, 0.12]
zs = np.arange(0.74, 0.96, 0.01)
for u in us:
    a = rear_curve(V0, u + 1e-5, zs) * 1000; b = rear_curve(V1, u + 1e-5, zs) * 1000
    print(f'u={u:.2f}  z:     ' + ' '.join(f'{z:5.2f}' for z in zs))
    print(f'        start: ' + ' '.join(f'{v:5.1f}' for v in a))
    print(f'        {tag:6s}: ' + ' '.join(f'{v:5.1f}' for v in b))
    print(f'        delta: ' + ' '.join(f'{v:5.1f}' for v in (b - a)))
