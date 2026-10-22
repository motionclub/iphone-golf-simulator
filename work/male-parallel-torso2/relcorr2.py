"""Per-region form correlation: interior of the torso only, finer DoG bands. python3.13 relcorr2.py tag..."""
import sys, json
import numpy as np
sys.path.insert(0, '.')
from relcorr import *
REG = {'chest': (1.15, 1.32), 'abdomen': (0.90, 1.15), 'pelvis': (0.80, 0.90)}
def corr_reg(view, tag, z0, z1, xhalf, s1, s2):
    mesh = Image.open(R / f'work/male-parallel-torso2/r/{tag}/{view}.png').convert('L')
    a, b = dog(PL, s1, s2), dog(mesh, s1, s2); m = torso_mask(view, z0, z1, xhalf)
    x, y = a[m], b[m]; return float(np.corrcoef(x, y)[0, 1])
if __name__ == '__main__':
    for (s1, s2) in ((1.2, 5.0), (2.0, 8.0)):
        print(f'--- DoG sigma {s1}/{s2}  (|x|<0.12)')
        for t in sys.argv[1:]:
            row = []
            for v in ('front', 'back'):
                for rn, (z0, z1) in REG.items():
                    row.append(f'{v[0]}-{rn[:3]} {corr_reg(v, t, z0, z1, 0.12, s1, s2):+.3f}')
            print(f'{t:7s}', ' | '.join(row))
