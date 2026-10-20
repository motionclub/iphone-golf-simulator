"""Banding / ripple detector on the Unity-clay (or plate) band-passed shading.
double-pec-line: number of distinct dark horizontal minima (prominence >= frac * main-crease depth) in the pec zone z 1.08-1.34, mean over columns |x| in .06-.14.
belt-line: longest run of consecutive columns (|x|<0.15) darker than -tau in any abdomen row z 0.86-1.12 (fraction of the 0.30 m width).
back ring-lines: same belt metric on the back, z 0.90-1.30.
python3.13 banding3.py <tag|plate> ..."""
import sys, json
import numpy as np
sys.path.insert(0, '.')
from relcorr import *
from PIL import Image
def hpimg(tag, view):
    img = PL if tag == 'plate' else Image.open(R / f'work/male-parallel-torso3/r/{tag}c/{view}.png').convert('L')
    return dog(img, 1.2, 5.0)
def prof_cols(a, view, xs, zs):
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; out = np.zeros((len(xs), len(zs)))
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            row = int(round(c['sole_y'] - z / mpp)); col = int(round(c['centre_x'] + x / mpp)); out[i, j] = a[row - 1:row + 2, col - 1:col + 2].mean()
    return out
def minima(v, zs, prom_abs, win=6):
    res = []
    for k in range(win, len(v) - win):
        if v[k] == v[k - win:k + win + 1].min():
            left = v[max(0, k - 3 * win):k].max() if k > 0 else v[k]; right = v[k + 1:k + 3 * win + 1].max()
            if min(left, right) - v[k] >= prom_abs: res.append((round(float(zs[k]), 3), round(float(min(left, right) - v[k]), 2)))
    return res
def measure(tag):
    out = {}
    a = hpimg(tag, 'front'); zs = np.arange(1.06, 1.35, 0.004); xs = [-0.14, -0.12, -0.10, -0.08, -0.06, 0.06, 0.08, 0.10, 0.12, 0.14]
    P = prof_cols(a, 'front', xs, zs); v = P.mean(0)
    main = max(1e-6, v[(zs > 1.14) & (zs < 1.22)].max() - v[(zs > 1.14) & (zs < 1.22)].min())
    out['pec_minima_abs'] = minima(v, zs, prom_abs=1.5)                  # absolute prominence 1.5 (DoG lum units)
    # count per-column minima deeper than 35% of the main crease depth
    cnt = []
    for i in range(len(xs)):
        m = minima(P[i], zs, prom_abs=0.35 * main); cnt.append(len(m))
    out['pec_double_line_cols'] = int(sum(1 for c_ in cnt if c_ >= 2)); out['pec_minima_per_col'] = cnt; out['main_crease_depth'] = round(float(main), 2)
    # belt line (front abdomen): fraction of width continuously darker than -tau
    zs2 = np.arange(0.86, 1.12, 0.004); xs2 = np.arange(-0.15, 0.1501, 0.004); P2 = prof_cols(a, 'front', xs2, zs2); tau = 3.0
    runs = []
    for j in range(len(zs2)):
        d = P2[:, j] < -tau; best = cur = 0
        for b in d:
            cur = cur + 1 if b else 0; best = max(best, cur)
        runs.append(best * 0.004 / 0.30)
    out['belt_front_max_frac'] = round(float(max(runs)), 3)
    b = hpimg(tag, 'back'); zs3 = np.arange(0.90, 1.30, 0.004); P3 = prof_cols(b, 'back', xs2, zs3); runs = []
    for j in range(len(zs3)):
        d = P3[:, j] < -tau; best = cur = 0
        for bb in d:
            cur = cur + 1 if bb else 0; best = max(best, cur)
        runs.append(best * 0.004 / 0.30)
    out['ring_back_max_frac'] = round(float(max(runs)), 3)
    return out
if __name__ == '__main__':
    for t in sys.argv[1:]: print(t, json.dumps(measure(t)))
