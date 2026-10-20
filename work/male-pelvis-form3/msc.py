"""multi-scale luminance correlation (clay renders r/<tag>_m/{back,front}.png vs plate) in the pelvis boxes: DoG scales fine/medium/coarse + raw-luminance zscore corr.
python3 msc.py tag..."""
import sys, numpy as np
sys.path.insert(0, '.')
from PIL import Image
import metric as MT, relcorr as RC
SC = {'fine(1.2/5)': (1.2, 5.0), 'med(3/10)': (3.0, 10.0), 'coarse(6/20)': (6.0, 20.0)}
REG = {'back_lowcheek z.76-.84': ('back', 0.76, 0.84), 'back_midcheek z.80-.90': ('back', 0.80, 0.90), 'back_pelvis z.80-.90 (gate)': ('back', 0.80, 0.90), 'front_pelvis z.80-.90': ('front', 0.80, 0.90), 'front_groin z.74-.84': ('front', 0.74, 0.84)}
def run(tag):
    MT.render(tag); out = {}
    for v in ('back', 'front'):
        mesh = Image.open(MT.W / f'r/{tag}_m/{v}.png').convert('L')
        for sn, (s1, s2) in SC.items():
            A, B = RC.dog(RC.PL, s1, s2), RC.dog(mesh, s1, s2)
            for rn, (vv, z0, z1) in REG.items():
                if vv != v: continue
                m = RC.torso_mask(v, z0, z1, 0.12); out[(rn, sn)] = float(np.corrcoef(A[m], B[m])[0, 1])
    return out
if __name__ == '__main__':
    rows = {t: run(t) for t in sys.argv[1:]}
    keys = list(next(iter(rows.values())).keys()); print('region / scale'.ljust(48) + ''.join(f'{t:>9s}' for t in rows))
    for k in keys: print(f'{k[0][:30]:32s} {k[1]:15s}' + ''.join(f'{rows[t][k]:9.3f}' for t in rows))
