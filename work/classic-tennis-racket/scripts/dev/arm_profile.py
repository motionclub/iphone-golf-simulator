"""Where are the hands? Arm axis, wrist (min cross-section), hand extents, finger/palm layout."""
import sys, json
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
for tag, xmin in (('male', 0.30), ('female', 0.12)):
    d = np.load(W + f'data/{tag}_body.npz')
    co, tris = d['co'], d['tris']
    print('=' * 20, tag, co.shape, 'bbox', co.min(0).round(3), co.max(0).round(3))
    for side, sgn in (('R(-x)', -1),):
        sel = np.where((sgn * co[:, 0] > xmin) & (co[:, 2] < 1.3))[0]
        P = co[sel]
        print(side, 'arm verts', len(sel), 'x range', P[:, 0].min().round(3), P[:, 0].max().round(3), 'z range', P[:, 2].min().round(3), P[:, 2].max().round(3))
        # lowest points of the arm = hand tips
        order = np.argsort(P[:, 2])
        print('  lowest 5 pts', P[order[:5]].round(4).tolist())
        tip = P[order[0]]
        # slice by z in 2 cm bands from the tip upwards: x/y extents and counts
        for z0 in np.arange(tip[2], tip[2] + 0.50, 0.02):
            m = (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.02)
            if m.sum() == 0:
                continue
            Q = P[m]
            print(f'  z[{z0:.3f},{z0+.02:.3f}) n={m.sum():4d} x[{Q[:,0].min():+.3f},{Q[:,0].max():+.3f}] y[{Q[:,1].min():+.3f},{Q[:,1].max():+.3f}] w_x={Q[:,0].max()-Q[:,0].min():.3f} w_y={Q[:,1].max()-Q[:,1].min():.3f}')
