"""Orthographic plate views (plain plate front/back, 2.87 mm/px), vertex normals, visibility, SH lighting fit.  numpy + Pillow; run with Blender's python3.13."""
import sys, json, pickle
from pathlib import Path
import numpy as np
from PIL import Image
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); W = R / 'work/male-parallel-torso3'
CAM = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
PLATE = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')).astype(np.float64)
F = pickle.load(open(W / 'baseline/faces.pkl', 'rb'))
def gblur(a, s):
    k = int(max(1, round(3 * s))); xs = np.arange(-k, k + 1); w = np.exp(-0.5 * (xs / s) ** 2); w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 1, a)
def bilinear(img, col, row):
    h, w = img.shape; c = np.clip(col, 0, w - 1.001); r = np.clip(row, 0, h - 1.001); c0 = np.floor(c).astype(int); r0 = np.floor(r).astype(int); fc = c - c0; fr = r - r0
    return img[r0, c0] * (1 - fc) * (1 - fr) + img[r0, c0 + 1] * fc * (1 - fr) + img[r0 + 1, c0] * (1 - fc) * fr + img[r0 + 1, c0 + 1] * fc * fr
class View:
    def __init__(self, name):      # name: 'front' | 'back'
        self.name = name; c = CAM['bald_' + name]; self.cx = c['centre_x']; self.sy = c['sole_y']; self.mpp = c['metres_per_pixel']; self.back = name == 'back'
        self.toward = np.array([0, 1.0, 0]) * (1 if self.back else -1) * -1 if False else (np.array([0, -1.0, 0]) if name == 'front' else np.array([0, 1.0, 0]))   # direction from the surface TOWARD the camera
        self.right = np.array([1.0, 0, 0]) * (-1 if self.back else 1)
    def project(self, P):
        return self.cx + (P[:, 0] * (-1 if self.back else 1)) / self.mpp, self.sy - P[:, 2] / self.mpp
    def depth(self, P): return P @ self.toward          # larger = closer to the camera
def vertex_normals(V, weight='angle', smooth=1):
    n = np.zeros_like(V)
    for f in F:
        m = len(f); p = V[f]
        fn = np.zeros(3)
        for k in range(1, m - 1): fn += np.cross(p[k] - p[0], p[k + 1] - p[0])
        ln = np.linalg.norm(fn)
        if ln < 1e-18: continue
        fn /= ln
        for k in range(m):
            a = p[(k + 1) % m] - p[k]; b = p[(k - 1) % m] - p[k]
            ang = np.arccos(np.clip(a @ b / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-18), -1, 1)) if weight == 'angle' else 0.5 * ln
            n[f[k]] += fn * ang
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
    return n
def zbuffer(view, P, sel, res=2.0, rad=2):
    col, row = view.project(P[sel]); dep = view.depth(P[sel]); H, Wd = int(720 * res), int(1280 * res)
    zb = np.full((H, Wd), -1e9); ci = np.clip(np.round(col * res).astype(int), 0, Wd - 1); ri = np.clip(np.round(row * res).astype(int), 0, H - 1)
    np.maximum.at(zb, (ri, ci), dep); out = zb.copy()
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1): out = np.maximum(out, np.roll(np.roll(zb, dy, 0), dx, 1))
    return out, res
def visible(view, P, N, sel=None, tol=0.006, mincos=0.12):
    sel = np.ones(len(P), bool) if sel is None else sel
    zb, res = zbuffer(view, P, sel); col, row = view.project(P); dep = view.depth(P)
    ci = np.clip(np.round(col * res).astype(int), 0, zb.shape[1] - 1); ri = np.clip(np.round(row * res).astype(int), 0, zb.shape[0] - 1)
    return sel & (dep >= zb[ri, ci] - tol) & ((N @ view.toward) > mincos)
def sh2(N):
    x, y, z = N[:, 0], N[:, 1], N[:, 2]
    return np.stack([np.ones_like(x), x, y, z, x * y, y * z, 3 * z * z - 1, x * z, x * x - y * y], axis=1)

# ---------------------------------------------------------------------------------------------------------------------------------
# yaw views of the multi-angle sheet (5.8 mm/px), camera-relative lighting
SHEET = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(np.float64)
class ViewYaw:
    def __init__(self, name, az, col0, mpp, sole_row, zmin=0.00247):
        self.name = name; self.az = az; a = np.radians(az); self.right = np.array([np.cos(a), np.sin(a), 0.0]); self.toward = np.array([np.sin(a), -np.cos(a), 0.0])
        self.col0 = col0; self.mpp = mpp; self.sole = sole_row; self.zmin = zmin; self.back = False
    def project(self, P): return self.col0 + (P @ self.right) / self.mpp, self.sole - (P[:, 2] - self.zmin) / self.mpp
    def depth(self, P): return P @ self.toward
def sh2c(N, vw):
    """camera-frame x-symmetric SH2 basis (right, up, toward) for any view"""
    nr = N @ vw.right if hasattr(vw, 'right') else N[:, 0]; nt = N @ vw.toward; nu = N[:, 2]
    return np.stack([np.ones_like(nr), nt, nu, nt * nu, 3 * nu * nu - 1, nr * nr - nt * nt], 1)
def zbuffer_gen(view, P, sel, res=2.0, rad=2, shape=(720, 1280)):
    col, row = view.project(P[sel]); dep = view.depth(P[sel]); H, Wd = int(shape[0] * res), int(shape[1] * res)
    zb = np.full((H, Wd), -1e9); ci = np.clip(np.round(col * res).astype(int), 0, Wd - 1); ri = np.clip(np.round(row * res).astype(int), 0, H - 1)
    np.maximum.at(zb, (ri, ci), dep); out = zb.copy()
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1): out = np.maximum(out, np.roll(np.roll(zb, dy, 0), dx, 1))
    return out, res
def visible_gen(view, P, N, sel=None, tol=0.006, mincos=0.12, res=2.0, rad=2):
    sel = np.ones(len(P), bool) if sel is None else sel
    zb, res = zbuffer_gen(view, P, sel, res=res, rad=rad); col, row = view.project(P); dep = view.depth(P)
    ci = np.clip(np.round(col * res).astype(int), 0, zb.shape[1] - 1); ri = np.clip(np.round(row * res).astype(int), 0, zb.shape[0] - 1)
    return sel & (dep >= zb[ri, ci] - tol) & ((N @ view.toward) > mincos)
