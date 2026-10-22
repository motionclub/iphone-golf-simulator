"""benv5.py: back envelope (max y over |x|<.19 vertices, thin z slab) vs plate silhouette (sub-pixel table, torso anchor).  import benv5; benv5.table(co, label)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
FB = np.load(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data/plate_back_fine4.npy')

def env(co, zs, hw=0.0045):
    out = []
    for z in zs:
        m = (np.abs(co[:, 2] - z) < hw) & (np.abs(co[:, 0]) < 0.19) & (co[:, 1] > 0)
        out.append(co[m, 1].max() if m.any() else np.nan)
    return np.array(out)

def table(items, zs=np.arange(0.62, 0.96, 0.02)):
    cols = [env(c, zs) for _, c in items]
    print('  z   plate   ' + '  '.join(f'{n:>7s}' for n, _ in items) + '   (mm; model - plate in brackets for the last)')
    for i, z in enumerate(zs):
        pl = np.interp(z, FB[0], FB[1]) * 1000 if (z >= 0.70 and z <= 1.18) else np.nan
        row = '  '.join(f'{1000*c[i]:7.1f}' for c in cols)
        print(f'{z:.2f} {pl:7.1f}   {row}   [{1000*cols[-1][i]-pl:+5.1f}]')
