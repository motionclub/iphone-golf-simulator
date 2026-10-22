"""Arm centre line of the right arm for both bodies: slices along the shoulder->wrist direction (numpy only)."""
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
for tag, xcut, zlow in (('male', -0.26, 0.95), ('female', -0.185, 0.80)):
    d = np.load(W + f'data/{tag}_body.npz')
    co = d['co']
    print('=' * 8, tag)
    # arm vertices: lateral of xcut (right = -x), z between zlow(hand start) and shoulder top (1.45)
    m = (co[:, 0] < xcut) & (co[:, 2] > zlow) & (co[:, 2] < 1.45)
    P = co[m]
    # fit direction from the lowest cluster (wrist) to the highest cluster (shoulder)
    lo = P[P[:, 2] < zlow + 0.04].mean(0)
    hi = P[P[:, 2] > np.percentile(P[:, 2], 92)].mean(0)
    ax = (hi - lo) / np.linalg.norm(hi - lo)
    print('lo', lo.round(3), 'hi', hi.round(3), 'axis (to shoulder)', ax.round(3))
    t = (P - lo) @ ax
    cl = []
    for t0 in np.arange(0.0, t.max(), 0.02):
        s = (t >= t0) & (t < t0 + 0.02)
        if s.sum() < 8: continue
        Q = P[s]
        c = Q.mean(0)
        # cross-section extents perpendicular to the axis
        e1 = np.cross(ax, [0, 1, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
        a1 = (Q - c) @ e1; a2 = (Q - c) @ e2
        cl.append((t0, c, a1.max() - a1.min(), a2.max() - a2.min()))
        print(f'  t={t0:.2f} n={s.sum():4d} centre {c.round(3)} width1 {a1.max()-a1.min():.3f} width2 {a2.max()-a2.min():.3f}')
