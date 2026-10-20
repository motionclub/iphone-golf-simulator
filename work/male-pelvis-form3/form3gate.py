"""Torso FORM3 gate metric (Unity-clay band-pass r, |x|<0.12, DoG 1.2/5) on this chat's clay renders (metric.render -> r/<tag>_m/{front,back}.png).
python3 form3gate.py <tag...>"""
import sys, json
import numpy as np
from PIL import Image
import metric as MT
import relcorr as RC
REG3 = {'chest': (1.15, 1.32), 'abdomen': (0.90, 1.15), 'pelvis': (0.80, 0.90)}
def run(tag):
    MT.render(tag); row = {}
    for v in ('front', 'back'):
        mesh = Image.open(MT.W / f'r/{tag}_m/{v}.png').convert('L'); A_, B_ = RC.dog(RC.PL, 1.2, 5.0), RC.dog(mesh, 1.2, 5.0)
        for rn, (z0, z1) in REG3.items(): m = RC.torso_mask(v, z0, z1, 0.12); row[f'{v}_{rn}'] = round(float(np.corrcoef(A_[m], B_[m])[0, 1]), 3)
    row['mean'] = round(float(np.mean(list(row.values()))), 3); return row
if __name__ == '__main__':
    for t in sys.argv[1:]: print(f'{t:8s}', run(t))
