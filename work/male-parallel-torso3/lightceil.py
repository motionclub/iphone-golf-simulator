"""Lighting-mismatch ceiling: r between the Unity-like clay render and the plate-SH-lit render of the SAME mesh (so shape error is zero)."""
import sys
sys.path.insert(0, '.')
from relcorr2 import *
tag = sys.argv[1]; sh_tag = sys.argv[2]
for (s1, s2) in ((1.2, 5.0), (2.0, 8.0)):
    out = {}
    for v in ('front', 'back'):
        A = Image.open(R / f'work/male-parallel-torso3/r/{tag}/{v}.png').convert('L'); B = Image.open(R / f'work/male-parallel-torso3/r/{sh_tag}/{v}.png').convert('L')
        da, db = dog(A, s1, s2), dog(B, s1, s2)
        for rn, (z0, z1) in REG.items():
            m = torso_mask(v, z0, z1, 0.12); out[f'{v[0]}-{rn[:3]}'] = round(float(np.corrcoef(da[m], db[m])[0, 1]), 3)
    print(f'DoG {s1}/{s2}: r(Unity-clay, plate-lit) same mesh:', out, 'mean %.3f' % np.mean(list(out.values())))
