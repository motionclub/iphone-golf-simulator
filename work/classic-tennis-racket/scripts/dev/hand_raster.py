"""Rasterise the right hand in its PCA frame (u fingers down the image, v across, w depth) to PNG-able PPM files.
Two images per hand: palm-side depth (nearest to +w) and dorsal-side depth. numpy only."""
import os
import sys
import numpy as np

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'


def raster(Q, tris, res=0.001, pad=0.01, side=+1):
    """z-buffer of w*side (largest = nearest). Q: (n,3) coords (u,v,w). returns (H,Wd) depth image + origin."""
    u0, v0 = Q[:, 0].min() - pad, Q[:, 1].min() - pad
    H = int((Q[:, 0].max() + pad - u0) / res) + 1
    Wd = int((Q[:, 1].max() + pad - v0) / res) + 1
    zb = np.full((H, Wd), -np.inf)
    for t in tris:
        a, b, c = Q[t[0]], Q[t[1]], Q[t[2]]
        xs = np.array([a[1], b[1], c[1]]); ys = np.array([a[0], b[0], c[0]])
        x0, x1 = int((xs.min() - v0) / res), int((xs.max() - v0) / res) + 1
        y0, y1 = int((ys.min() - u0) / res), int((ys.max() - u0) / res) + 1
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        px = v0 + (gx + 0.5) * res; py = u0 + (gy + 0.5) * res
        d = (b[0] - c[0]) * (a[1] - c[1]) + (c[1] - b[1]) * (a[0] - c[0])
        if abs(d) < 1e-14:
            continue
        l1 = ((b[0] - c[0]) * (px - c[1]) + (c[1] - b[1]) * (py - c[0])) / d
        l2 = ((c[0] - a[0]) * (px - c[1]) + (a[1] - c[1]) * (py - c[0])) / d
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        if not m.any():
            continue
        z = side * (l1 * a[2] + l2 * b[2] + l3 * c[2])
        yy, xx = gy[m], gx[m]
        ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < Wd)
        yy, xx, z = yy[ok], xx[ok], z[m][ok]
        cur = zb[yy, xx]
        zb[yy, xx] = np.maximum(cur, z)
    return zb, (u0, v0, res)


def write_ppm(path, zb):
    m = np.isfinite(zb)
    img = np.zeros(zb.shape + (3,), np.uint8)
    if m.any():
        lo, hi = zb[m].min(), zb[m].max()
        g = ((zb - lo) / (hi - lo + 1e-12))
        img[m] = (np.clip(g[m], 0, 1)[:, None] * 200 + 40).astype(np.uint8)
    with open(path, 'wb') as f:
        f.write(b'P6 %d %d 255\n' % (zb.shape[1], zb.shape[0]))
        f.write(img.tobytes())


if __name__ == '__main__':
    d = np.load(W + 'data/male_body.npz')
    co, tris = d['co'], d['tris']
    sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
    idx = -np.ones(len(co), int); idx[sel] = np.arange(len(sel))
    keep = np.all(idx[tris] >= 0, axis=1)
    T = idx[tris[keep]]
    P = co[sel]
    c = P.mean(0)
    U, S, Vt = np.linalg.svd(P - c, full_matrices=False)
    u, v = Vt[0], Vt[1]
    if u[2] > 0: u = -u
    if v[1] > 0: v = -v
    w = np.cross(u, v)
    Q = np.stack([(P - c) @ u, (P - c) @ v, (P - c) @ w], 1)
    os.makedirs(W + 'tmp', exist_ok=True)
    np.savez(W + 'tmp/male_hand_frame.npz', c=c, u=u, v=v, w=w)
    for name, side in (('palm', -1), ('dorsal', +1)):      # +w is the DORSAL side (palm normal = -w = medial)
        zb, org = raster(Q, T, res=0.001, side=side)
        if name == 'palm':
            zb = zb[:, ::-1]       # view from the palm side: mirror so +v (thumb) is on the left like a real palm view
        write_ppm(W + f'tmp/male_hand_{name}.ppm', zb)
        print(name, zb.shape, org)
